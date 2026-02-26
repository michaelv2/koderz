from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import duckdb

from agentmon.models.events import Alert, DNSEvent, Severity


def _extract_tld(domain: str) -> str:
    parts = domain.rsplit(".", 1)
    return parts[-1] if len(parts) >= 2 else domain


def _extract_registered_domain(domain: str) -> str:
    parts = domain.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return domain


class EventStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[duckdb.DuckDBPyConnection] = None

    def connect(self):
        self.conn = duckdb.connect(self.db_path)
        self._create_schema()

    def _create_schema(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS dns_events (
                id VARCHAR PRIMARY KEY,
                timestamp TIMESTAMP,
                client VARCHAR,
                domain VARCHAR,
                domain_tld VARCHAR,
                domain_registered VARCHAR,
                query_type VARCHAR,
                blocked BOOLEAN
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id VARCHAR PRIMARY KEY,
                timestamp TIMESTAMP,
                severity VARCHAR,
                title VARCHAR,
                description VARCHAR,
                source_event_type VARCHAR,
                client VARCHAR,
                domain VARCHAR,
                analyzer VARCHAR,
                confidence DOUBLE,
                llm_analysis VARCHAR,
                acknowledged BOOLEAN DEFAULT FALSE
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS domain_baseline (
                client VARCHAR,
                domain VARCHAR,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                query_count INTEGER DEFAULT 0,
                PRIMARY KEY (client, domain)
            )
        """)

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def insert_dns_event(self, event: DNSEvent) -> str:
        event_id = str(uuid.uuid4())
        tld = _extract_tld(event.domain)
        registered = _extract_registered_domain(event.domain)
        self.conn.execute(
            "INSERT INTO dns_events (id, timestamp, client, domain, domain_tld, domain_registered, query_type, blocked) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [event_id, event.timestamp, event.client, event.domain, tld, registered, event.query_type, event.blocked],
        )
        return event_id

    def insert_dns_events_batch(self, events: list[DNSEvent]) -> int:
        count = 0
        for event in events:
            self.insert_dns_event(event)
            count += 1
        return count

    def update_domain_baseline(self, client: str, domain: str, timestamp: datetime):
        existing = self.conn.execute(
            "SELECT query_count FROM domain_baseline WHERE client = ? AND domain = ?",
            [client, domain],
        ).fetchone()
        if existing is None:
            self.conn.execute(
                "INSERT INTO domain_baseline (client, domain, first_seen, last_seen, query_count) "
                "VALUES (?, ?, ?, ?, 1)",
                [client, domain, timestamp, timestamp],
            )
        else:
            self.conn.execute(
                "UPDATE domain_baseline SET last_seen = ?, query_count = query_count + 1 "
                "WHERE client = ? AND domain = ?",
                [timestamp, client, domain],
            )

    def is_domain_known(self, client: str, domain: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM domain_baseline WHERE client = ? AND domain = ?",
            [client, domain],
        ).fetchone()
        return row is not None

    def insert_alert(self, alert: Alert) -> str:
        self.conn.execute(
            "INSERT INTO alerts (id, timestamp, severity, title, description, source_event_type, "
            "client, domain, analyzer, confidence, llm_analysis, acknowledged) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                alert.id, alert.timestamp, alert.severity.value, alert.title,
                alert.description, alert.source_event_type, alert.client,
                alert.domain, alert.analyzer, alert.confidence,
                alert.llm_analysis, alert.acknowledged,
            ],
        )
        return alert.id

    def get_unacknowledged_alerts(
        self, min_severity: str = "info", limit: int = 50
    ) -> list[dict[str, Any]]:
        severity_order = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
        min_level = severity_order.get(min_severity, 0)

        rows = self.conn.execute(
            "SELECT id, timestamp, severity, title, description, source_event_type, "
            "client, domain, analyzer, confidence, llm_analysis, acknowledged "
            "FROM alerts WHERE acknowledged = FALSE "
            "ORDER BY timestamp DESC LIMIT ?",
            [limit],
        ).fetchall()

        results = []
        for row in rows:
            sev = row[2]
            if severity_order.get(sev, 0) >= min_level:
                results.append({
                    "id": row[0],
                    "timestamp": row[1],
                    "severity": row[2],
                    "title": row[3],
                    "description": row[4],
                    "source_event_type": row[5],
                    "client": row[6],
                    "domain": row[7],
                    "analyzer": row[8],
                    "confidence": row[9],
                    "llm_analysis": row[10],
                    "acknowledged": row[11],
                })
        return results

    def mark_domain_blocked(self, domain: str, max_age_seconds: Optional[int] = None) -> bool:
        if max_age_seconds is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)
            row = self.conn.execute(
                "SELECT id FROM dns_events WHERE domain = ? AND blocked = FALSE AND timestamp >= ? "
                "ORDER BY timestamp DESC LIMIT 1",
                [domain, cutoff],
            ).fetchone()
        else:
            row = self.conn.execute(
                "SELECT id FROM dns_events WHERE domain = ? AND blocked = FALSE "
                "ORDER BY timestamp DESC LIMIT 1",
                [domain],
            ).fetchone()
        if row is None:
            return False
        self.conn.execute(
            "UPDATE dns_events SET blocked = TRUE WHERE id = ?",
            [row[0]],
        )
        return True

    def cleanup_old_data(self, dns_days: int = 30, alerts_days: int = 30) -> dict[str, int]:
        dns_cutoff = datetime.now(timezone.utc) - timedelta(days=dns_days)
        alerts_cutoff = datetime.now(timezone.utc) - timedelta(days=alerts_days)

        dns_before = self.conn.execute("SELECT COUNT(*) FROM dns_events").fetchone()[0]
        self.conn.execute("DELETE FROM dns_events WHERE timestamp < ?", [dns_cutoff])
        dns_after = self.conn.execute("SELECT COUNT(*) FROM dns_events").fetchone()[0]

        alerts_before = self.conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
        self.conn.execute("DELETE FROM alerts WHERE timestamp < ?", [alerts_cutoff])
        alerts_after = self.conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]

        return {
            "dns_events": dns_before - dns_after,
            "alerts": alerts_before - alerts_after,
        }

    def get_client_stats(self, hours: int = 24) -> list[dict[str, Any]]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        rows = self.conn.execute(
            "SELECT client, COUNT(*) as query_count, "
            "COUNT(DISTINCT domain) as unique_domains, "
            "SUM(CASE WHEN blocked THEN 1 ELSE 0 END) as blocked_count "
            "FROM dns_events WHERE timestamp >= ? "
            "GROUP BY client",
            [cutoff],
        ).fetchall()
        return [
            {
                "client": row[0],
                "query_count": row[1],
                "unique_domains": row[2],
                "blocked_count": row[3],
            }
            for row in rows
        ]
