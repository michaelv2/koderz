"""
Acceptance test suite for the agentmon clone.

This test suite is written BEFORE either implementation run (frontier baseline
or orchestrated) and must be held constant across both approaches. Neither run
may modify these tests.

The tests validate the core detection pipeline:
  - Data models and DuckDB storage
  - Syslog receiver and parser
  - Detection engine (entropy, DGA, known-bad patterns, baseline analysis)
  - LLM classifier and threat intelligence
  - CLI, alerting, and configuration

Tests are organized by subtask to allow incremental validation during the
orchestrated run. Each subtask's tests are independent (use fresh DB/state)
so they can run in any order.

Requirements:
  pip install pytest pytest-asyncio duckdb httpx click

Run:
  pytest tests/test_agentmon_acceptance.py -v
"""

import asyncio
import json
import math
import os
import socket
import struct
import tempfile
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# The tests import from an "agentmon" package. The clone must expose these
# exact module paths and class/function names. This is the public contract.
# ---------------------------------------------------------------------------

# ===================================================================
# SUBTASK 1: Data models + storage layer
# ===================================================================


class TestDataModels:
    """Verify core data models exist with expected fields and behavior."""

    def test_severity_ordering(self):
        """Severity enum has 5 levels in ascending order."""
        from agentmon.models.events import Severity

        levels = [Severity.INFO, Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        assert len(levels) == 5
        # Values should be string representations
        assert Severity.INFO.value == "info"
        assert Severity.CRITICAL.value == "critical"

    def test_dns_event_creation(self):
        """DNSEvent holds timestamp, client, domain, query_type, blocked."""
        from agentmon.models.events import DNSEvent

        ts = datetime.now(timezone.utc)
        event = DNSEvent(
            timestamp=ts,
            client="192.168.1.100",
            domain="example.com",
            query_type="A",
            blocked=False,
        )
        assert event.timestamp == ts
        assert event.client == "192.168.1.100"
        assert event.domain == "example.com"
        assert event.query_type == "A"
        assert event.blocked is False

    def test_dns_event_domain_parts(self):
        """DNSEvent.domain_parts() splits domain into labels."""
        from agentmon.models.events import DNSEvent

        event = DNSEvent(
            timestamp=datetime.now(timezone.utc),
            client="10.0.0.1",
            domain="sub.example.co.uk",
            query_type="A",
            blocked=False,
        )
        parts = event.domain_parts()
        assert parts == ["sub", "example", "co", "uk"]

    def test_dns_event_is_immutable(self):
        """DNSEvent should be frozen (immutable)."""
        from agentmon.models.events import DNSEvent

        event = DNSEvent(
            timestamp=datetime.now(timezone.utc),
            client="10.0.0.1",
            domain="example.com",
            query_type="A",
            blocked=False,
        )
        with pytest.raises((AttributeError, TypeError)):
            event.domain = "other.com"

    def test_alert_creation(self):
        """Alert holds all required fields including optional llm_analysis."""
        from agentmon.models.events import Alert, Severity

        alert = Alert(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            severity=Severity.HIGH,
            title="Known-bad domain",
            description="c2-server.evil.com matches known-bad pattern",
            source_event_type="dns",
            client="192.168.1.100",
            domain="c2-server.evil.com",
            analyzer="dns_baseline",
            confidence=0.95,
        )
        assert alert.severity == Severity.HIGH
        assert alert.confidence == 0.95
        assert alert.llm_analysis is None
        assert alert.acknowledged is False

    def test_alert_severity_is_mutable(self):
        """Alert severity can be modified (for LLM downgrade)."""
        from agentmon.models.events import Alert, Severity

        alert = Alert(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            severity=Severity.HIGH,
            title="Test",
            description="Test alert",
            source_event_type="dns",
        )
        alert.severity = Severity.LOW
        assert alert.severity == Severity.LOW

    def test_connection_event_creation(self):
        """ConnectionEvent holds network connection metadata."""
        from agentmon.models.events import ConnectionEvent

        event = ConnectionEvent(
            timestamp=datetime.now(timezone.utc),
            client="192.168.1.100",
            src_port=54321,
            dst_ip="93.184.216.34",
            dst_port=443,
            protocol="tcp",
        )
        assert event.dst_port == 443
        assert event.bytes_sent == 0  # default


class TestEventStore:
    """Verify DuckDB storage layer operations."""

    @pytest.fixture
    def db_path(self, tmp_path):
        return str(tmp_path / "test_events.db")

    @pytest.fixture
    def store(self, db_path):
        from agentmon.storage.db import EventStore

        s = EventStore(db_path)
        s.connect()
        yield s
        s.close()

    def test_schema_creation(self, store):
        """EventStore creates required tables on connect."""
        result = store.conn.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'main' ORDER BY table_name"
        ).fetchall()
        table_names = {row[0] for row in result}
        assert "dns_events" in table_names
        assert "alerts" in table_names
        assert "domain_baseline" in table_names

    def test_insert_and_retrieve_dns_event(self, store):
        """Insert a DNS event and verify it's stored with derived fields."""
        from agentmon.models.events import DNSEvent

        event = DNSEvent(
            timestamp=datetime.now(timezone.utc),
            client="192.168.1.50",
            domain="api.github.com",
            query_type="A",
            blocked=False,
        )
        event_id = store.insert_dns_event(event)
        assert event_id is not None

        row = store.conn.execute(
            "SELECT client, domain, domain_tld, domain_registered, blocked "
            "FROM dns_events WHERE id = ?",
            [event_id],
        ).fetchone()
        assert row is not None
        assert row[0] == "192.168.1.50"
        assert row[1] == "api.github.com"
        assert row[2] == "com"  # TLD derived
        assert row[3] == "github.com"  # registered domain derived
        assert row[4] is False

    def test_batch_insert(self, store):
        """Batch insert multiple events."""
        from agentmon.models.events import DNSEvent

        events = [
            DNSEvent(
                timestamp=datetime.now(timezone.utc),
                client="10.0.0.1",
                domain=f"host{i}.example.com",
                query_type="A",
                blocked=False,
            )
            for i in range(10)
        ]
        count = store.insert_dns_events_batch(events)
        assert count == 10

        total = store.conn.execute("SELECT COUNT(*) FROM dns_events").fetchone()[0]
        assert total == 10

    def test_baseline_upsert(self, store):
        """Baseline updates: first call creates, second increments query_count."""
        ts = datetime.now(timezone.utc)
        store.update_domain_baseline("client-a", "example.com", ts)

        row = store.conn.execute(
            "SELECT query_count FROM domain_baseline "
            "WHERE client = 'client-a' AND domain = 'example.com'"
        ).fetchone()
        assert row[0] == 1

        store.update_domain_baseline("client-a", "example.com", ts + timedelta(hours=1))
        row = store.conn.execute(
            "SELECT query_count FROM domain_baseline "
            "WHERE client = 'client-a' AND domain = 'example.com'"
        ).fetchone()
        assert row[0] == 2

    def test_is_domain_known(self, store):
        """is_domain_known returns True only after baseline entry exists."""
        assert store.is_domain_known("client-b", "new-domain.com") is False
        store.update_domain_baseline(
            "client-b", "new-domain.com", datetime.now(timezone.utc)
        )
        assert store.is_domain_known("client-b", "new-domain.com") is True

    def test_insert_and_query_alert(self, store):
        """Insert an alert and retrieve it as unacknowledged."""
        from agentmon.models.events import Alert, Severity

        alert = Alert(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            severity=Severity.HIGH,
            title="Test alert",
            description="Test description",
            source_event_type="dns",
            client="10.0.0.5",
            domain="evil.com",
            analyzer="dns_baseline",
            confidence=0.9,
        )
        alert_id = store.insert_alert(alert)
        assert alert_id is not None

        alerts = store.get_unacknowledged_alerts(min_severity="medium", limit=10)
        assert len(alerts) >= 1
        assert any(a["domain"] == "evil.com" for a in alerts)

    def test_block_correlation(self, store):
        """mark_domain_blocked correlates with recent unblocked query."""
        from agentmon.models.events import DNSEvent

        event = DNSEvent(
            timestamp=datetime.now(timezone.utc),
            client="192.168.1.10",
            domain="blocked.example.com",
            query_type="A",
            blocked=False,
        )
        event_id = store.insert_dns_event(event)

        result = store.mark_domain_blocked("blocked.example.com", max_age_seconds=5)
        assert result is True

        row = store.conn.execute(
            "SELECT blocked FROM dns_events WHERE id = ?", [event_id]
        ).fetchone()
        assert row[0] is True

    def test_block_correlation_expired(self, store):
        """mark_domain_blocked fails if no recent query within time window."""
        from agentmon.models.events import DNSEvent

        old_ts = datetime.now(timezone.utc) - timedelta(seconds=30)
        event = DNSEvent(
            timestamp=old_ts,
            client="192.168.1.10",
            domain="old-blocked.example.com",
            query_type="A",
            blocked=False,
        )
        store.insert_dns_event(event)

        result = store.mark_domain_blocked("old-blocked.example.com", max_age_seconds=5)
        assert result is False

    def test_cleanup_old_data(self, store):
        """cleanup_old_data deletes events older than retention period."""
        from agentmon.models.events import DNSEvent

        old_event = DNSEvent(
            timestamp=datetime.now(timezone.utc) - timedelta(days=60),
            client="10.0.0.1",
            domain="old.example.com",
            query_type="A",
            blocked=False,
        )
        new_event = DNSEvent(
            timestamp=datetime.now(timezone.utc),
            client="10.0.0.1",
            domain="new.example.com",
            query_type="A",
            blocked=False,
        )
        store.insert_dns_event(old_event)
        store.insert_dns_event(new_event)

        counts = store.cleanup_old_data(dns_days=30, alerts_days=30)
        assert counts["dns_events"] >= 1

        total = store.conn.execute("SELECT COUNT(*) FROM dns_events").fetchone()[0]
        assert total == 1  # only the new event remains

    def test_client_stats(self, store):
        """get_client_stats returns per-client query counts and block rates."""
        from agentmon.models.events import DNSEvent

        ts = datetime.now(timezone.utc)
        for domain in ["a.com", "b.com", "c.com"]:
            store.insert_dns_event(
                DNSEvent(
                    timestamp=ts,
                    client="stats-client",
                    domain=domain,
                    query_type="A",
                    blocked=(domain == "c.com"),
                )
            )

        stats = store.get_client_stats(hours=1)
        client_stat = [s for s in stats if s["client"] == "stats-client"]
        assert len(client_stat) == 1
        assert client_stat[0]["query_count"] == 3
        assert client_stat[0]["unique_domains"] == 3

    def test_context_manager(self, db_path):
        """EventStore works as context manager."""
        from agentmon.storage.db import EventStore

        with EventStore(db_path) as store:
            result = store.conn.execute("SELECT 1").fetchone()
            assert result[0] == 1


# ===================================================================
# SUBTASK 2: Syslog receiver + parsers
# ===================================================================


class TestSyslogParsing:
    """Verify syslog message parsing for RFC 3164 and 5424."""

    def test_parse_rfc3164(self):
        """Parse standard RFC 3164 syslog message."""
        from agentmon.collectors.syslog_receiver import parse_syslog_message

        raw = "<30>Feb 10 12:34:56 pihole dnsmasq[123]: query[A] example.com from 192.168.1.50"
        msg = parse_syslog_message(raw)
        assert msg is not None
        assert msg.hostname == "pihole"
        assert "dnsmasq" in msg.tag
        assert "example.com" in msg.message

    def test_parse_rfc5424(self):
        """Parse RFC 5424 structured syslog message."""
        from agentmon.collectors.syslog_receiver import parse_syslog_message

        raw = "<30>1 2026-02-10T12:34:56Z pihole dnsmasq 123 - - query[A] test.com from 10.0.0.1"
        msg = parse_syslog_message(raw)
        assert msg is not None
        assert msg.hostname == "pihole"

    def test_parse_fallback(self):
        """Malformed message falls back to raw text."""
        from agentmon.collectors.syslog_receiver import parse_syslog_message

        msg = parse_syslog_message("just some random text")
        assert msg is not None
        assert "random text" in msg.message

    def test_priority_decoding(self):
        """Priority byte decodes to facility and severity."""
        from agentmon.collectors.syslog_receiver import parse_syslog_message

        # Priority 30 = facility 3 (daemon), severity 6 (informational)
        msg = parse_syslog_message("<30>Feb 10 12:00:00 host app: test")
        assert msg.facility == 3
        assert msg.severity == 6

    def test_oversized_message_handled(self):
        """Messages exceeding max size are handled gracefully."""
        from agentmon.collectors.syslog_receiver import parse_syslog_message

        huge = "<30>Feb 10 12:00:00 host app: " + "x" * 10000
        # Should not raise; may truncate or return None
        result = parse_syslog_message(huge)
        # Either parsed (possibly truncated) or gracefully rejected
        assert result is None or hasattr(result, "message")


class TestPiholeParser:
    """Verify Pi-hole/dnsmasq log parsing."""

    def _make_syslog_msg(self, tag, message):
        from agentmon.collectors.syslog_receiver import SyslogMessage

        return SyslogMessage(
            timestamp=datetime.now(timezone.utc),
            hostname="pihole",
            tag=tag,
            message=message,
        )

    def test_parse_dns_query(self):
        """Parse dnsmasq query line into DNSEvent."""
        from agentmon.collectors.syslog_parsers import PiholeParser

        parser = PiholeParser()
        msg = self._make_syslog_msg("dnsmasq", "query[A] example.com from 192.168.1.100")
        dns, conn = parser.parse(msg)
        assert dns is not None
        assert dns.domain == "example.com"
        assert dns.client == "192.168.1.100"
        assert dns.query_type == "A"
        assert dns.blocked is False

    def test_parse_aaaa_query(self):
        """Parse AAAA query type."""
        from agentmon.collectors.syslog_parsers import PiholeParser

        parser = PiholeParser()
        msg = self._make_syslog_msg("dnsmasq", "query[AAAA] ipv6.example.com from 10.0.0.5")
        dns, _ = parser.parse(msg)
        assert dns is not None
        assert dns.query_type == "AAAA"

    def test_parse_blocked_with_client(self):
        """Parse gravity-blocked domain with client IP."""
        from agentmon.collectors.syslog_parsers import PiholeParser

        parser = PiholeParser()
        msg = self._make_syslog_msg(
            "dnsmasq", "gravity blocked ads.tracker.com from 192.168.1.100"
        )
        dns, _ = parser.parse(msg)
        assert dns is not None
        assert dns.domain == "ads.tracker.com"
        assert dns.blocked is True
        assert dns.client == "192.168.1.100"

    def test_parse_blocked_without_client(self):
        """Block notification without client produces special marker."""
        from agentmon.collectors.syslog_parsers import PiholeParser

        parser = PiholeParser()
        msg = self._make_syslog_msg(
            "dnsmasq", "gravity blocked ads.example.com is 0.0.0.0"
        )
        dns, _ = parser.parse(msg)
        assert dns is not None
        assert dns.client == "__BLOCK_NOTIFICATION__"
        assert dns.blocked is True

    def test_forward_reply_ignored(self):
        """Forward and reply lines return None (not DNS events)."""
        from agentmon.collectors.syslog_parsers import PiholeParser

        parser = PiholeParser()
        for line in [
            "forwarded example.com to 8.8.8.8",
            "reply example.com is 93.184.216.34",
        ]:
            msg = self._make_syslog_msg("dnsmasq", line)
            dns, conn = parser.parse(msg)
            assert dns is None

    def test_tag_detection(self):
        """Parser recognizes dnsmasq-related tags."""
        from agentmon.collectors.syslog_parsers import PiholeParser

        parser = PiholeParser()
        for tag in ["dnsmasq", "dnsmasq-dhcp", "pihole-FTL", "pihole"]:
            assert parser.can_parse(tag) is True
        assert parser.can_parse("kernel") is False


class TestMessageRouting:
    """Verify syslog message routing to correct parser."""

    def test_dns_query_routed(self):
        """DNS query message routes to PiholeParser and produces DNSEvent."""
        from agentmon.collectors.syslog_parsers import route_message
        from agentmon.collectors.syslog_receiver import SyslogMessage

        msg = SyslogMessage(
            timestamp=datetime.now(timezone.utc),
            hostname="pihole",
            tag="dnsmasq",
            message="query[A] test.com from 10.0.0.1",
        )
        dns, conn = route_message(msg)
        assert dns is not None
        assert conn is None

    def test_unrecognized_tag_returns_none(self):
        """Messages with unrecognized tags return (None, None)."""
        from agentmon.collectors.syslog_parsers import route_message
        from agentmon.collectors.syslog_receiver import SyslogMessage

        msg = SyslogMessage(
            timestamp=datetime.now(timezone.utc),
            hostname="somehost",
            tag="cron",
            message="some cron job output",
        )
        dns, conn = route_message(msg)
        assert dns is None
        assert conn is None


class TestSyslogReceiver:
    """Verify async syslog receiver accepts TCP and UDP connections."""

    def _free_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    @pytest.mark.asyncio
    async def test_tcp_receive(self):
        """TCP syslog receiver accepts connection and invokes handler."""
        from agentmon.collectors.syslog_receiver import SyslogConfig, SyslogReceiver

        received = []
        port = self._free_port()

        async def handler(msg):
            received.append(msg)

        config = SyslogConfig(port=port, protocol="tcp", bind_address="127.0.0.1")
        receiver = SyslogReceiver(config, handler)
        await receiver.start()

        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            line = b"<30>Feb 10 12:00:00 pihole dnsmasq[1]: query[A] tcp-test.com from 10.0.0.1\n"
            writer.write(line)
            await writer.drain()
            writer.close()
            await writer.wait_closed()

            await asyncio.sleep(0.3)
            assert len(received) >= 1
            assert "tcp-test.com" in received[0].message
        finally:
            await receiver.stop()

    @pytest.mark.asyncio
    async def test_udp_receive(self):
        """UDP syslog receiver accepts datagrams and invokes handler."""
        from agentmon.collectors.syslog_receiver import SyslogConfig, SyslogReceiver

        received = []
        port = self._free_port()

        async def handler(msg):
            received.append(msg)

        config = SyslogConfig(port=port, protocol="udp", bind_address="127.0.0.1")
        receiver = SyslogReceiver(config, handler)
        await receiver.start()

        try:
            transport, _ = await asyncio.get_event_loop().create_datagram_endpoint(
                asyncio.DatagramProtocol, remote_addr=("127.0.0.1", port)
            )
            line = b"<30>Feb 10 12:00:00 pihole dnsmasq[1]: query[A] udp-test.com from 10.0.0.2"
            transport.sendto(line)

            await asyncio.sleep(0.3)
            assert len(received) >= 1
            assert "udp-test.com" in received[0].message
        finally:
            transport.close()
            await receiver.stop()

    @pytest.mark.asyncio
    async def test_ip_allowlist(self):
        """Connections from non-allowed IPs are rejected."""
        from agentmon.collectors.syslog_receiver import SyslogConfig, SyslogReceiver

        received = []
        port = self._free_port()

        async def handler(msg):
            received.append(msg)

        # Allow only 10.0.0.1 — our localhost connection should be rejected
        config = SyslogConfig(
            port=port,
            protocol="tcp",
            bind_address="127.0.0.1",
            allowed_ips=["10.0.0.1"],
        )
        receiver = SyslogReceiver(config, handler)
        await receiver.start()

        try:
            try:
                reader, writer = await asyncio.open_connection("127.0.0.1", port)
                writer.write(b"<30>Feb 10 12:00:00 host app: blocked\n")
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            except ConnectionError:
                pass  # Connection refused is also acceptable

            await asyncio.sleep(0.3)
            assert len(received) == 0
        finally:
            await receiver.stop()

    @pytest.mark.asyncio
    async def test_graceful_shutdown(self):
        """Receiver stops cleanly and reports is_running=False."""
        from agentmon.collectors.syslog_receiver import SyslogConfig, SyslogReceiver

        port = self._free_port()
        config = SyslogConfig(port=port, protocol="tcp", bind_address="127.0.0.1")
        receiver = SyslogReceiver(config, lambda msg: None)
        await receiver.start()
        assert receiver.is_running is True

        await receiver.stop()
        assert receiver.is_running is False


# ===================================================================
# SUBTASK 3: Detection engine
# ===================================================================


class TestEntropy:
    """Verify Shannon entropy and DGA detection."""

    def test_entropy_empty_string(self):
        """Empty string has zero entropy."""
        from agentmon.analyzers.entropy import calculate_entropy

        assert calculate_entropy("") == 0.0

    def test_entropy_single_char(self):
        """Repeated single character has zero entropy."""
        from agentmon.analyzers.entropy import calculate_entropy

        assert calculate_entropy("aaaa") == 0.0

    def test_entropy_two_equal_chars(self):
        """Two equally frequent characters have entropy 1.0."""
        from agentmon.analyzers.entropy import calculate_entropy

        assert abs(calculate_entropy("ab") - 1.0) < 0.01

    def test_entropy_random_string_is_high(self):
        """Random alphanumeric string has high entropy (>3.0)."""
        from agentmon.analyzers.entropy import calculate_entropy

        assert calculate_entropy("k8xp2m9qr7w4zt1v") > 3.0

    def test_domain_entropy_strips_tld(self):
        """Domain entropy calculation strips common TLDs."""
        from agentmon.analyzers.entropy import calculate_domain_entropy

        # "google" has low entropy; the .com should be stripped
        entropy = calculate_domain_entropy("google.com")
        assert entropy < 3.0

    def test_high_entropy_domain_normal(self):
        """Normal domains are not flagged as high entropy."""
        from agentmon.analyzers.entropy import is_high_entropy_domain

        flagged, _ = is_high_entropy_domain("google.com")
        assert flagged is False

    def test_high_entropy_domain_random(self):
        """Random-looking domain is flagged as high entropy."""
        from agentmon.analyzers.entropy import is_high_entropy_domain

        flagged, entropy = is_high_entropy_domain("xk9p2mq7rw4zt1vbn.com")
        assert flagged is True
        assert entropy > 3.5

    def test_high_entropy_short_domain_not_flagged(self):
        """Short domains are never flagged regardless of entropy."""
        from agentmon.analyzers.entropy import is_high_entropy_domain

        flagged, _ = is_high_entropy_domain("xk9.com")
        assert flagged is False

    def test_excessive_consonants(self):
        """Consonant-heavy string is detected."""
        from agentmon.analyzers.entropy import has_excessive_consonants

        assert has_excessive_consonants("xkcd-mngmnt-prblm.com") is True
        assert has_excessive_consonants("facebook.com") is False

    def test_dga_detection_normal_domains(self):
        """Legitimate domains are not flagged as DGA."""
        from agentmon.analyzers.entropy import looks_like_dga

        for domain in ["google.com", "api.github.com", "cdn.cloudflare.net"]:
            is_dga, reasons = looks_like_dga(domain)
            assert is_dga is False, f"{domain} incorrectly flagged as DGA"

    def test_dga_detection_obvious_dga(self):
        """Obvious DGA domain is flagged with multiple reasons."""
        from agentmon.analyzers.entropy import looks_like_dga

        is_dga, reasons = looks_like_dga("xk9p2mq7rw4zt1vbn3cx.com")
        assert is_dga is True
        assert len(reasons) >= 2

    def test_dga_requires_two_signals(self):
        """Single high-entropy signal alone does not trigger DGA."""
        from agentmon.analyzers.entropy import looks_like_dga

        # This domain has high entropy but may not trigger other signals
        is_dga, reasons = looks_like_dga("abcdefghijklmno.com")
        # Even if is_dga is True, it must have >= 2 reasons
        if is_dga:
            assert len(reasons) >= 2


class TestKnownBadPatterns:
    """Verify label-boundary pattern matching for known-bad domains."""

    def test_pattern_at_domain_start(self):
        """Pattern at start of domain matches."""
        from agentmon.analyzers.dns_baseline import DNSBaselineAnalyzer

        assert DNSBaselineAnalyzer._matches_at_label_boundary(
            "c2-server.evil.com", "c2-"
        ) is True

    def test_pattern_after_dot(self):
        """Pattern immediately after a dot matches."""
        from agentmon.analyzers.dns_baseline import DNSBaselineAnalyzer

        assert DNSBaselineAnalyzer._matches_at_label_boundary(
            "sub.c2-server.evil.com", "c2-"
        ) is True

    def test_pattern_mid_label_no_match(self):
        """Pattern in the middle of a label does NOT match."""
        from agentmon.analyzers.dns_baseline import DNSBaselineAnalyzer

        # "c2-" appears inside "ec2-" — must NOT match
        assert DNSBaselineAnalyzer._matches_at_label_boundary(
            "ec2-35-169-254-100.compute-1.amazonaws.com", "c2-"
        ) is False

    def test_aws_ec2_not_flagged(self):
        """Real AWS EC2 reverse DNS should not match c2- pattern."""
        from agentmon.analyzers.dns_baseline import DNSBaselineAnalyzer

        for domain in [
            "ec2-35-169-254-100.compute-1.amazonaws.com",
            "ec2-54-234-89-123.us-east-1.compute.amazonaws.com",
        ]:
            assert DNSBaselineAnalyzer._matches_at_label_boundary(domain, "c2-") is False

    def test_actual_c2_domain_flagged(self):
        """Actual C2 domains are flagged."""
        from agentmon.analyzers.dns_baseline import DNSBaselineAnalyzer

        for domain in ["c2-server.evil.com", "beacon.malware.net"]:
            matched = (
                DNSBaselineAnalyzer._matches_at_label_boundary(domain, "c2-")
                or DNSBaselineAnalyzer._matches_at_label_boundary(domain, "beacon")
            )
            assert matched is True

    def test_case_insensitive(self):
        """Pattern matching is case-insensitive."""
        from agentmon.analyzers.dns_baseline import DNSBaselineAnalyzer

        assert DNSBaselineAnalyzer._matches_at_label_boundary(
            "C2-Server.Evil.com", "c2-"
        ) is True

    def test_rat_in_integrate_no_match(self):
        """'rat-' pattern should not match inside 'integrate-api'."""
        from agentmon.analyzers.dns_baseline import DNSBaselineAnalyzer

        assert DNSBaselineAnalyzer._matches_at_label_boundary(
            "integrate-api.service.com", "rat-"
        ) is False


class TestDNSBaselineAnalyzer:
    """Verify baseline learning, detection, and alert generation."""

    @pytest.fixture
    def store(self, tmp_path):
        from agentmon.storage.db import EventStore

        s = EventStore(str(tmp_path / "test.db"))
        s.connect()
        yield s
        s.close()

    @pytest.fixture
    def analyzer_config(self):
        from agentmon.analyzers.dns_baseline import AnalyzerConfig

        return AnalyzerConfig(
            known_bad_patterns=["c2-", "beacon", "malware"],
            allowlist={"safe.example.com"},
            ignore_suffixes=[".local", ".lan", ".arpa"],
            learning_mode=False,
            llm_enabled=False,
        )

    @pytest.fixture
    def analyzer(self, store, analyzer_config):
        from agentmon.analyzers.dns_baseline import DNSBaselineAnalyzer

        return DNSBaselineAnalyzer(store, analyzer_config)

    def test_known_bad_generates_high_alert(self, analyzer):
        """Known-bad domain produces HIGH severity alert."""
        from agentmon.models.events import DNSEvent, Severity

        event = DNSEvent(
            timestamp=datetime.now(timezone.utc),
            client="10.0.0.1",
            domain="c2-server.evil.com",
            query_type="A",
            blocked=False,
        )
        alerts = analyzer.analyze_event(event)
        high_alerts = [a for a in alerts if a.severity == Severity.HIGH]
        assert len(high_alerts) >= 1
        assert high_alerts[0].confidence >= 0.9

    def test_allowlisted_domain_no_alert(self, analyzer):
        """Allowlisted domain produces no alerts."""
        from agentmon.models.events import DNSEvent

        event = DNSEvent(
            timestamp=datetime.now(timezone.utc),
            client="10.0.0.1",
            domain="safe.example.com",
            query_type="A",
            blocked=False,
        )
        alerts = analyzer.analyze_event(event)
        assert len(alerts) == 0

    def test_ignored_suffix_no_alert(self, analyzer):
        """Domains with ignored suffixes produce no alerts."""
        from agentmon.models.events import DNSEvent

        event = DNSEvent(
            timestamp=datetime.now(timezone.utc),
            client="10.0.0.1",
            domain="printer.local",
            query_type="A",
            blocked=False,
        )
        alerts = analyzer.analyze_event(event)
        assert len(alerts) == 0

    def test_new_domain_info_alert(self, analyzer):
        """First-seen domain in detection mode produces INFO alert."""
        from agentmon.models.events import DNSEvent, Severity

        event = DNSEvent(
            timestamp=datetime.now(timezone.utc),
            client="10.0.0.1",
            domain="never-seen-before.example.com",
            query_type="A",
            blocked=False,
        )
        alerts = analyzer.analyze_event(event)
        new_domain_alerts = [a for a in alerts if a.severity == Severity.INFO]
        assert len(new_domain_alerts) >= 1

    def test_learning_mode_suppresses_new_domain_alerts(self, store):
        """Learning mode does NOT alert on new domains, but still updates baseline."""
        from agentmon.analyzers.dns_baseline import AnalyzerConfig, DNSBaselineAnalyzer
        from agentmon.models.events import DNSEvent, Severity

        config = AnalyzerConfig(
            known_bad_patterns=["c2-"],
            learning_mode=True,
            llm_enabled=False,
        )
        analyzer = DNSBaselineAnalyzer(store, config)

        event = DNSEvent(
            timestamp=datetime.now(timezone.utc),
            client="learner",
            domain="new-in-learning.example.com",
            query_type="A",
            blocked=False,
        )
        alerts = analyzer.analyze_event(event)

        # No new-domain alerts in learning mode
        info_alerts = [a for a in alerts if a.severity == Severity.INFO]
        assert len(info_alerts) == 0

        # But baseline was still updated
        assert store.is_domain_known("learner", "new-in-learning.example.com") is True

    def test_learning_mode_still_alerts_known_bad(self, store):
        """Learning mode still alerts on known-bad patterns."""
        from agentmon.analyzers.dns_baseline import AnalyzerConfig, DNSBaselineAnalyzer
        from agentmon.models.events import DNSEvent, Severity

        config = AnalyzerConfig(
            known_bad_patterns=["c2-"],
            learning_mode=True,
            llm_enabled=False,
        )
        analyzer = DNSBaselineAnalyzer(store, config)

        event = DNSEvent(
            timestamp=datetime.now(timezone.utc),
            client="learner",
            domain="c2-payload.bad.com",
            query_type="A",
            blocked=False,
        )
        alerts = analyzer.analyze_event(event)
        assert any(a.severity == Severity.HIGH for a in alerts)

    def test_dga_domain_medium_alert(self, analyzer):
        """DGA-like domain produces MEDIUM severity alert."""
        from agentmon.models.events import DNSEvent, Severity

        event = DNSEvent(
            timestamp=datetime.now(timezone.utc),
            client="10.0.0.1",
            domain="xk9p2mq7rw4zt1vbn3cx.com",
            query_type="A",
            blocked=False,
        )
        alerts = analyzer.analyze_event(event)
        # Should have at least a DGA or entropy alert
        dga_alerts = [a for a in alerts if a.severity in (Severity.MEDIUM, Severity.LOW)]
        assert len(dga_alerts) >= 1

    def test_alert_deduplication(self, analyzer):
        """Duplicate alerts within dedup window are suppressed."""
        from agentmon.models.events import DNSEvent

        event = DNSEvent(
            timestamp=datetime.now(timezone.utc),
            client="10.0.0.1",
            domain="c2-repeat.evil.com",
            query_type="A",
            blocked=False,
        )
        alerts1 = analyzer.analyze_event(event)
        alerts2 = analyzer.analyze_event(event)

        # First call produces alerts, second should be deduplicated
        assert len(alerts1) > 0
        assert len(alerts2) == 0 or len(alerts2) < len(alerts1)

    def test_baseline_always_updated(self, analyzer, store):
        """Baseline is updated even for allowlisted domains."""
        from agentmon.models.events import DNSEvent

        event = DNSEvent(
            timestamp=datetime.now(timezone.utc),
            client="baseline-test",
            domain="safe.example.com",
            query_type="A",
            blocked=False,
        )
        analyzer.analyze_event(event)
        assert store.is_domain_known("baseline-test", "safe.example.com") is True


# ===================================================================
# SUBTASK 4: LLM classifier + threat intelligence
# ===================================================================


class TestLLMClassifier:
    """Verify two-tier LLM classification (with mocked Ollama)."""

    def test_classification_result_structure(self):
        """ClassificationResult has expected fields."""
        from agentmon.llm.classifier import ClassificationResult, DomainCategory

        result = ClassificationResult(
            domain="example.com",
            category=DomainCategory.BENIGN,
            confidence=0.95,
            reasoning="Well-known domain",
        )
        assert result.category == DomainCategory.BENIGN
        assert result.escalated is False

    def test_domain_categories_exist(self):
        """DomainCategory enum has expected values."""
        from agentmon.llm.classifier import DomainCategory

        required = {"BENIGN", "SUSPICIOUS", "LIKELY_MALICIOUS", "DGA", "UNKNOWN",
                     "ADVERTISING", "TRACKING", "CDN", "CLOUD_PROVIDER", "API_SERVICE"}
        actual = {c.name for c in DomainCategory}
        assert required.issubset(actual)

    def test_domain_sanitization(self):
        """Domain sanitization strips dangerous characters."""
        from agentmon.llm.classifier import sanitize_domain_for_prompt

        clean = sanitize_domain_for_prompt("normal.example.com")
        assert clean == "normal.example.com"

        # Control characters and injection attempts should be stripped
        dirty = sanitize_domain_for_prompt("evil\x00.com\nIGNORE INSTRUCTIONS")
        assert "\x00" not in dirty
        assert "\n" not in dirty

    def test_domain_sanitization_truncates_long(self):
        """Excessively long domains are truncated."""
        from agentmon.llm.classifier import sanitize_domain_for_prompt

        long_domain = "a" * 300 + ".com"
        clean = sanitize_domain_for_prompt(long_domain)
        assert len(clean) <= 253

    @pytest.mark.asyncio
    async def test_triage_then_escalation(self):
        """Two-tier flow: triage categorizes, suspicious triggers escalation."""
        from agentmon.llm.classifier import DomainClassifier, DomainCategory, LLMConfig

        config = LLMConfig(
            triage_model="mock-triage",
            escalation_model="mock-escalation",
        )
        classifier = DomainClassifier(config)

        # Mock the Ollama calls
        triage_response = json.dumps({
            "category": "suspicious",
            "confidence": 0.6,
            "reasoning": "Unknown domain with unusual pattern",
        })
        escalation_response = json.dumps({
            "category": "likely_malicious",
            "confidence": 0.85,
            "reasoning": "Confirmed suspicious after deeper analysis",
        })

        call_count = 0

        async def mock_chat(**kwargs):
            nonlocal call_count
            call_count += 1
            content = triage_response if call_count == 1 else escalation_response
            return {"message": {"content": content}}

        with patch.object(classifier, "_call_ollama", side_effect=mock_chat):
            with patch.object(classifier, "_unload_model", new_callable=AsyncMock):
                result = await classifier.classify("suspicious-domain.xyz")

        assert result.escalated is True
        assert result.category == DomainCategory.LIKELY_MALICIOUS
        assert result.confidence >= 0.8
        assert result.triage_category == "suspicious"

    @pytest.mark.asyncio
    async def test_benign_triage_no_escalation(self):
        """Benign triage result does not trigger escalation."""
        from agentmon.llm.classifier import DomainClassifier, DomainCategory, LLMConfig

        config = LLMConfig(
            triage_model="mock-triage",
            escalation_model="mock-escalation",
        )
        classifier = DomainClassifier(config)

        response = json.dumps({
            "category": "benign",
            "confidence": 0.95,
            "reasoning": "Well-known CDN domain",
        })

        async def mock_chat(**kwargs):
            return {"message": {"content": response}}

        with patch.object(classifier, "_call_ollama", side_effect=mock_chat):
            with patch.object(classifier, "_unload_model", new_callable=AsyncMock):
                result = await classifier.classify("cdn.cloudflare.com")

        assert result.escalated is False
        assert result.category == DomainCategory.BENIGN

    @pytest.mark.asyncio
    async def test_classification_caching(self):
        """Repeated classification of same domain uses cache."""
        from agentmon.llm.classifier import DomainClassifier, LLMConfig

        config = LLMConfig(triage_model="mock", escalation_model="mock")
        classifier = DomainClassifier(config)

        response = json.dumps({
            "category": "benign",
            "confidence": 0.9,
            "reasoning": "Known domain",
        })

        call_count = 0

        async def mock_chat(**kwargs):
            nonlocal call_count
            call_count += 1
            return {"message": {"content": response}}

        with patch.object(classifier, "_call_ollama", side_effect=mock_chat):
            with patch.object(classifier, "_unload_model", new_callable=AsyncMock):
                await classifier.classify("cached-domain.com")
                await classifier.classify("cached-domain.com")

        assert call_count == 1  # second call used cache


class TestThreatFeeds:
    """Verify threat feed download, parsing, and domain lookup."""

    def test_domain_extraction_from_url(self, tmp_path):
        """Feed parser extracts domains from URLs."""
        from agentmon.threat_feeds import ThreatFeedManager

        # Create a mock feed cache file
        cache_dir = tmp_path / "feeds"
        cache_dir.mkdir()
        feed_file = cache_dir / "urlhaus.txt"
        feed_file.write_text(
            "# URLhaus feed\n"
            "http://malware-host.evil.com/payload.exe\n"
            "http://c2.badsite.net/beacon\n"
            "# Comment line\n"
            "\n"
            "http://192.168.1.1/not-a-domain\n"
        )

        manager = ThreatFeedManager(cache_dir=str(cache_dir))
        manager._load_cache(str(feed_file))
        domains = manager.get_malicious_domains()

        assert "malware-host.evil.com" in domains
        assert "c2.badsite.net" in domains
        # Bare IPs should be skipped
        assert "192.168.1.1" not in domains

    def test_domain_check_exact_match(self, tmp_path):
        """check_domain finds exact domain match."""
        from agentmon.threat_feeds import ThreatFeedManager

        cache_dir = tmp_path / "feeds"
        cache_dir.mkdir()
        feed_file = cache_dir / "urlhaus.txt"
        feed_file.write_text("http://evil.example.com/malware\n")

        manager = ThreatFeedManager(cache_dir=str(cache_dir))
        manager._load_cache(str(feed_file))

        assert manager.check_domain("evil.example.com") is not None

    def test_domain_check_parent_match(self, tmp_path):
        """check_domain matches subdomains of known-bad domains."""
        from agentmon.threat_feeds import ThreatFeedManager

        cache_dir = tmp_path / "feeds"
        cache_dir.mkdir()
        feed_file = cache_dir / "urlhaus.txt"
        feed_file.write_text("http://evil.com/path\n")

        manager = ThreatFeedManager(cache_dir=str(cache_dir))
        manager._load_cache(str(feed_file))

        assert manager.check_domain("sub.evil.com") is not None

    def test_domain_check_clean_domain(self, tmp_path):
        """check_domain returns None for clean domains."""
        from agentmon.threat_feeds import ThreatFeedManager

        cache_dir = tmp_path / "feeds"
        cache_dir.mkdir()
        feed_file = cache_dir / "urlhaus.txt"
        feed_file.write_text("http://evil.com/path\n")

        manager = ThreatFeedManager(cache_dir=str(cache_dir))
        manager._load_cache(str(feed_file))

        assert manager.check_domain("google.com") is None


class TestVirusTotal:
    """Verify VirusTotal client (with mocked HTTP)."""

    def test_reputation_risk_score(self):
        """VirusTotalReputation computes risk score correctly."""
        from agentmon.threat_intel.virustotal import VirusTotalReputation

        rep = VirusTotalReputation(
            malicious=5, suspicious=2, undetected=10, harmless=50
        )
        # risk = (5*1.0 + 2*0.5) / (5+2+10+50) = 6.0/67 ≈ 0.0896
        assert abs(rep.risk_score - 6.0 / 67) < 0.001

    def test_reputation_high_risk(self):
        """High malicious count flags as high risk."""
        from agentmon.threat_intel.virustotal import VirusTotalReputation

        rep = VirusTotalReputation(malicious=5, suspicious=0, undetected=5, harmless=10)
        assert rep.is_high_risk is True

    def test_reputation_summary(self):
        """Summary string includes malicious and suspicious counts."""
        from agentmon.threat_intel.virustotal import VirusTotalReputation

        rep = VirusTotalReputation(malicious=3, suspicious=1, undetected=5, harmless=20)
        summary = rep.summary()
        assert "3 malicious" in summary
        assert "1 suspicious" in summary

    @pytest.mark.asyncio
    async def test_client_unavailable_without_key(self):
        """VirusTotal client reports unavailable when no API key."""
        from agentmon.threat_intel.virustotal import VirusTotalClient

        client = VirusTotalClient(api_key=None)
        assert client.available is False


# ===================================================================
# SUBTASK 5: CLI + alerting + configuration
# ===================================================================


class TestConfiguration:
    """Verify TOML config loading and environment variable overrides."""

    def test_load_example_config(self, tmp_path):
        """TOML config file loads without errors."""
        from agentmon.config import load_config

        config_file = tmp_path / "agentmon.toml"
        config_file.write_text(
            '[database]\npath = "/tmp/test.db"\n\n'
            '[syslog]\nport = 1514\nprotocol = "tcp"\n\n'
            '[analyzer]\nentropy_threshold = 3.5\nlearning_mode = false\n'
            'known_bad_patterns = ["c2-", "beacon"]\n\n'
            '[slack]\nenabled = true\nwebhook_url = "https://hooks.slack.com/test"\n'
        )
        config = load_config(str(config_file))
        assert config["database"]["path"] == "/tmp/test.db"
        assert config["syslog"]["port"] == 1514
        assert config["analyzer"]["known_bad_patterns"] == ["c2-", "beacon"]

    def test_env_var_override_slack(self, tmp_path):
        """AGENTMON_SLACK_WEBHOOK env var overrides config file."""
        from agentmon.config import load_config

        config_file = tmp_path / "agentmon.toml"
        config_file.write_text('[slack]\nenabled = false\nwebhook_url = ""\n')

        with patch.dict(os.environ, {"AGENTMON_SLACK_WEBHOOK": "https://hooks.slack.com/env"}):
            config = load_config(str(config_file))
            assert config["slack"]["webhook_url"] == "https://hooks.slack.com/env"
            assert config["slack"]["enabled"] is True

    def test_missing_config_uses_defaults(self):
        """Missing config file produces usable defaults."""
        from agentmon.config import load_config

        config = load_config("/nonexistent/path/agentmon.toml")
        # Should return defaults without crashing
        assert "database" in config or isinstance(config, dict)


class TestClientResolver:
    """Verify client IP to hostname resolution."""

    def test_explicit_mapping(self):
        """Explicit IP->name mapping takes priority."""
        from agentmon.resolver import ClientResolver, ResolverConfig

        config = ResolverConfig(
            enabled=True,
            mappings={"192.168.1.100": "alice-laptop"},
        )
        resolver = ClientResolver(config)
        assert resolver.resolve("192.168.1.100") == "alice-laptop"

    def test_unknown_ip_returns_ip(self):
        """Unknown IP with no PTR record returns raw IP."""
        from agentmon.resolver import ClientResolver, ResolverConfig

        config = ResolverConfig(enabled=True)
        resolver = ClientResolver(config)
        # Use a non-routable IP that won't have PTR
        result = resolver.resolve("192.0.2.1")
        # Should return the IP itself (or resolved name if somehow available)
        assert result is not None

    def test_suffix_stripping(self):
        """Hostname suffix is stripped when configured."""
        from agentmon.resolver import ClientResolver, ResolverConfig

        config = ResolverConfig(
            enabled=True,
            strip_suffix=True,
            mappings={"10.0.0.1": "myhost.home.lan"},
        )
        resolver = ClientResolver(config)
        # With strip_suffix, "myhost.home.lan" -> "myhost"
        result = resolver.resolve("10.0.0.1")
        assert result == "myhost"

    def test_cache_stats(self):
        """Cache stats reports mapping and cache counts."""
        from agentmon.resolver import ClientResolver, ResolverConfig

        config = ResolverConfig(
            enabled=True,
            mappings={"10.0.0.1": "host-a", "10.0.0.2": "host-b"},
        )
        resolver = ClientResolver(config)
        stats = resolver.get_cache_stats()
        assert stats["mappings"] == 2

    def test_disabled_resolver_returns_ip(self):
        """Disabled resolver passes through raw IP."""
        from agentmon.resolver import ClientResolver, ResolverConfig

        config = ResolverConfig(enabled=False)
        resolver = ClientResolver(config)
        assert resolver.resolve("192.168.1.50") == "192.168.1.50"


class TestSlackNotifier:
    """Verify Slack webhook alerting."""

    @pytest.mark.asyncio
    async def test_severity_filtering(self):
        """Alerts below min_severity are not sent."""
        from agentmon.models.events import Alert, Severity
        from agentmon.notifiers.slack import SlackConfig, SlackNotifier

        config = SlackConfig(
            webhook_url="https://hooks.slack.com/test",
            min_severity=Severity.MEDIUM,
        )
        notifier = SlackNotifier(config)

        low_alert = Alert(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            severity=Severity.LOW,
            title="Low alert",
            description="Should not be sent",
            source_event_type="dns",
        )

        # Mock httpx to verify no request is made
        with patch.object(notifier, "_client", new_callable=MagicMock) as mock_client:
            result = await notifier.send_alert(low_alert)
            assert result is False

    @pytest.mark.asyncio
    async def test_high_alert_formatted_and_sent(self):
        """HIGH alert is formatted with color and fields, then sent."""
        from agentmon.models.events import Alert, Severity
        from agentmon.notifiers.slack import SlackConfig, SlackNotifier

        config = SlackConfig(
            webhook_url="https://hooks.slack.com/test",
            min_severity=Severity.LOW,
        )
        notifier = SlackNotifier(config)

        alert = Alert(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            severity=Severity.HIGH,
            title="C2 domain detected",
            description="c2-server.evil.com matches known-bad pattern",
            source_event_type="dns",
            client="192.168.1.50",
            domain="c2-server.evil.com",
            analyzer="dns_baseline",
            confidence=0.95,
        )

        # Verify the format method produces valid Slack payload
        payload = notifier._format_message(alert)
        assert "attachments" in payload
        attachment = payload["attachments"][0]
        assert attachment["color"] in ("#ff0000", "danger", "#cc0000", "#d63232")  # red-ish
        assert "C2 domain detected" in attachment.get("title", attachment.get("fallback", ""))

    @pytest.mark.asyncio
    async def test_notifier_close(self):
        """Notifier close does not raise."""
        from agentmon.notifiers.slack import SlackConfig, SlackNotifier

        config = SlackConfig(webhook_url="https://hooks.slack.com/test")
        notifier = SlackNotifier(config)
        await notifier.close()  # should not raise


class TestCLI:
    """Verify Click CLI commands exist and accept expected arguments."""

    def test_cli_has_listen_command(self):
        """CLI exposes 'listen' command."""
        from click.testing import CliRunner

        from agentmon.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["listen", "--help"])
        assert result.exit_code == 0
        assert "--port" in result.output
        assert "--protocol" in result.output

    def test_cli_has_stats_command(self):
        """CLI exposes 'stats' command."""
        from click.testing import CliRunner

        from agentmon.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["stats", "--help"])
        assert result.exit_code == 0

    def test_cli_has_alerts_command(self):
        """CLI exposes 'alerts' command."""
        from click.testing import CliRunner

        from agentmon.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["alerts", "--help"])
        assert result.exit_code == 0

    def test_cli_has_baseline_command(self):
        """CLI exposes 'baseline' command."""
        from click.testing import CliRunner

        from agentmon.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["baseline", "--help"])
        assert result.exit_code == 0

    def test_cli_has_cleanup_command(self):
        """CLI exposes 'cleanup' command."""
        from click.testing import CliRunner

        from agentmon.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["cleanup", "--help"])
        assert result.exit_code == 0

    def test_cli_has_feeds_command(self):
        """CLI exposes 'feeds' command."""
        from click.testing import CliRunner

        from agentmon.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["feeds", "--help"])
        assert result.exit_code == 0

    def test_cli_listen_flags(self):
        """listen command accepts --learning and --llm flags."""
        from click.testing import CliRunner

        from agentmon.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["listen", "--help"])
        assert "--learning" in result.output
        assert "--llm" in result.output


# ===================================================================
# INTEGRATION TESTS (end-to-end pipeline)
# ===================================================================


class TestIntegration:
    """End-to-end tests: syslog message -> storage -> analysis -> alerts."""

    def _free_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    @pytest.fixture
    def store(self, tmp_path):
        from agentmon.storage.db import EventStore

        s = EventStore(str(tmp_path / "integration.db"))
        s.connect()
        yield s
        s.close()

    @pytest.mark.asyncio
    async def test_syslog_to_stored_event(self, store):
        """TCP syslog DNS query is parsed, stored, and retrievable."""
        from agentmon.analyzers.dns_baseline import AnalyzerConfig, DNSBaselineAnalyzer
        from agentmon.collectors.syslog_parsers import route_message
        from agentmon.collectors.syslog_receiver import SyslogConfig, SyslogReceiver

        analyzer = DNSBaselineAnalyzer(
            store,
            AnalyzerConfig(learning_mode=True, llm_enabled=False),
        )

        port = self._free_port()
        stored_events = []

        async def handle(msg):
            dns, conn = route_message(msg)
            if dns and dns.client != "__BLOCK_NOTIFICATION__":
                store.insert_dns_event(dns)
                stored_events.append(dns)
                analyzer.analyze_event(dns)

        config = SyslogConfig(port=port, protocol="tcp", bind_address="127.0.0.1")
        receiver = SyslogReceiver(config, handle)
        await receiver.start()

        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            line = (
                b"<30>Feb 10 12:00:00 pihole dnsmasq[1]: "
                b"query[A] integration-test.example.com from 192.168.1.42\n"
            )
            writer.write(line)
            await writer.drain()
            writer.close()
            await writer.wait_closed()

            await asyncio.sleep(0.5)

            assert len(stored_events) == 1
            assert stored_events[0].domain == "integration-test.example.com"

            # Verify it's in the database
            count = store.conn.execute(
                "SELECT COUNT(*) FROM dns_events WHERE domain = 'integration-test.example.com'"
            ).fetchone()[0]
            assert count == 1

            # Verify baseline was updated
            assert store.is_domain_known("192.168.1.42", "integration-test.example.com")
        finally:
            await receiver.stop()

    @pytest.mark.asyncio
    async def test_known_bad_generates_alert_end_to_end(self, store):
        """Known-bad domain flowing through full pipeline produces alert in DB."""
        from agentmon.analyzers.dns_baseline import AnalyzerConfig, DNSBaselineAnalyzer
        from agentmon.collectors.syslog_parsers import route_message
        from agentmon.collectors.syslog_receiver import SyslogConfig, SyslogReceiver

        analyzer = DNSBaselineAnalyzer(
            store,
            AnalyzerConfig(
                known_bad_patterns=["c2-", "beacon"],
                learning_mode=False,
                llm_enabled=False,
            ),
        )

        port = self._free_port()
        generated_alerts = []

        async def handle(msg):
            dns, conn = route_message(msg)
            if dns and dns.client != "__BLOCK_NOTIFICATION__":
                store.insert_dns_event(dns)
                alerts = analyzer.analyze_event(dns)
                for alert in alerts:
                    store.insert_alert(alert)
                    generated_alerts.append(alert)

        config = SyslogConfig(port=port, protocol="tcp", bind_address="127.0.0.1")
        receiver = SyslogReceiver(config, handle)
        await receiver.start()

        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            line = (
                b"<30>Feb 10 12:00:00 pihole dnsmasq[1]: "
                b"query[A] c2-server.evil.com from 192.168.1.99\n"
            )
            writer.write(line)
            await writer.drain()
            writer.close()
            await writer.wait_closed()

            await asyncio.sleep(0.5)

            assert len(generated_alerts) >= 1
            assert any(a.domain == "c2-server.evil.com" for a in generated_alerts)

            # Verify alert is in DB
            db_alerts = store.get_unacknowledged_alerts(min_severity="info", limit=10)
            assert any(a["domain"] == "c2-server.evil.com" for a in db_alerts)
        finally:
            await receiver.stop()

    @pytest.mark.asyncio
    async def test_block_correlation_end_to_end(self, store):
        """Query followed by block notification marks event as blocked."""
        from agentmon.collectors.syslog_parsers import route_message
        from agentmon.collectors.syslog_receiver import SyslogConfig, SyslogReceiver

        port = self._free_port()

        async def handle(msg):
            dns, conn = route_message(msg)
            if dns:
                if dns.client == "__BLOCK_NOTIFICATION__":
                    store.mark_domain_blocked(dns.domain)
                else:
                    store.insert_dns_event(dns)

        config = SyslogConfig(port=port, protocol="tcp", bind_address="127.0.0.1")
        receiver = SyslogReceiver(config, handle)
        await receiver.start()

        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", port)

            # First: the query event
            query_line = (
                b"<30>Feb 10 12:00:00 pihole dnsmasq[1]: "
                b"query[A] ads.tracker.com from 192.168.1.10\n"
            )
            writer.write(query_line)
            await writer.drain()
            await asyncio.sleep(0.2)

            # Then: the block notification
            block_line = (
                b"<30>Feb 10 12:00:00 pihole dnsmasq[1]: "
                b"gravity blocked ads.tracker.com is 0.0.0.0\n"
            )
            writer.write(block_line)
            await writer.drain()
            writer.close()
            await writer.wait_closed()

            await asyncio.sleep(0.5)

            # The stored event should now be marked as blocked
            row = store.conn.execute(
                "SELECT blocked FROM dns_events WHERE domain = 'ads.tracker.com'"
            ).fetchone()
            assert row is not None
            assert row[0] is True
        finally:
            await receiver.stop()

    @pytest.mark.asyncio
    async def test_multiple_clients_independent_baselines(self, store):
        """Different clients maintain independent baselines."""
        from agentmon.analyzers.dns_baseline import AnalyzerConfig, DNSBaselineAnalyzer
        from agentmon.models.events import DNSEvent

        analyzer = DNSBaselineAnalyzer(
            store,
            AnalyzerConfig(learning_mode=True, llm_enabled=False),
        )

        ts = datetime.now(timezone.utc)
        for client in ["client-a", "client-b"]:
            event = DNSEvent(
                timestamp=ts,
                client=client,
                domain="shared-domain.com",
                query_type="A",
                blocked=False,
            )
            analyzer.analyze_event(event)

        # Each client should have its own baseline entry
        assert store.is_domain_known("client-a", "shared-domain.com") is True
        assert store.is_domain_known("client-b", "shared-domain.com") is True

        # But client-c should not
        assert store.is_domain_known("client-c", "shared-domain.com") is False
