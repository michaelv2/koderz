from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from agentmon.analyzers.entropy import is_high_entropy_domain, looks_like_dga
from agentmon.models.events import Alert, DNSEvent, Severity
from agentmon.storage.db import EventStore


@dataclass
class AnalyzerConfig:
    known_bad_patterns: list[str] = field(default_factory=list)
    allowlist: set[str] = field(default_factory=set)
    ignore_suffixes: list[str] = field(default_factory=list)
    learning_mode: bool = False
    llm_enabled: bool = False
    entropy_threshold: float = 3.5
    dedup_ttl_seconds: float = 300.0


class DNSBaselineAnalyzer:
    def __init__(self, store: EventStore, config: AnalyzerConfig):
        self.store = store
        self.config = config
        self._dedup_cache: dict[str, float] = {}

    def analyze_event(self, event: DNSEvent) -> list[Alert]:
        alerts: list[Alert] = []

        # Always update baseline
        self.store.update_domain_baseline(
            event.client, event.domain, event.timestamp
        )

        # Check ignored suffixes
        for suffix in self.config.ignore_suffixes:
            if event.domain.endswith(suffix):
                return alerts

        # Check allowlist - no alerts but baseline was already updated
        if event.domain in self.config.allowlist:
            return alerts

        # Check known-bad patterns
        for pattern in self.config.known_bad_patterns:
            if self._matches_at_label_boundary(event.domain, pattern):
                alert = self._make_alert(
                    event,
                    severity=Severity.HIGH,
                    title=f"Known-bad pattern: {pattern}",
                    description=f"{event.domain} matches known-bad pattern '{pattern}'",
                    analyzer="known_bad_pattern",
                    confidence=0.95,
                )
                alerts.append(alert)
                break

        # Check DGA
        is_dga, dga_reasons = looks_like_dga(event.domain)
        if is_dga:
            alert = self._make_alert(
                event,
                severity=Severity.MEDIUM,
                title="Possible DGA domain",
                description=f"{event.domain}: {', '.join(dga_reasons)}",
                analyzer="dga_detection",
                confidence=0.7,
            )
            alerts.append(alert)
        else:
            # Check high entropy (even if not full DGA)
            high_ent, ent_val = is_high_entropy_domain(event.domain)
            if high_ent:
                alert = self._make_alert(
                    event,
                    severity=Severity.LOW,
                    title="High entropy domain",
                    description=f"{event.domain} entropy={ent_val:.2f}",
                    analyzer="entropy_detection",
                    confidence=0.5,
                )
                alerts.append(alert)

        # Check if domain is new (not in baseline before this call)
        # Since we already updated baseline above, check query_count
        row = self.store.conn.execute(
            "SELECT query_count FROM domain_baseline WHERE client = ? AND domain = ?",
            [event.client, event.domain],
        ).fetchone()
        is_first_seen = row is not None and row[0] == 1

        if is_first_seen and not self.config.learning_mode:
            # Only alert on new domains if not already covered by known-bad/DGA
            if not any(
                a.analyzer in ("known_bad_pattern", "dga_detection")
                for a in alerts
            ):
                alert = self._make_alert(
                    event,
                    severity=Severity.INFO,
                    title="New domain observed",
                    description=f"First time {event.client} queried {event.domain}",
                    analyzer="new_domain",
                    confidence=0.3,
                )
                alerts.append(alert)

        # Deduplicate
        alerts = self._deduplicate(alerts)

        return alerts

    def _make_alert(
        self,
        event: DNSEvent,
        severity: Severity,
        title: str,
        description: str,
        analyzer: str,
        confidence: float,
    ) -> Alert:
        return Alert(
            id=str(uuid.uuid4()),
            timestamp=event.timestamp,
            severity=severity,
            title=title,
            description=description,
            source_event_type="dns",
            client=event.client,
            domain=event.domain,
            analyzer=analyzer,
            confidence=confidence,
        )

    def _deduplicate(self, alerts: list[Alert]) -> list[Alert]:
        now = time.monotonic()
        # Clean expired entries
        self._dedup_cache = {
            k: v
            for k, v in self._dedup_cache.items()
            if now - v < self.config.dedup_ttl_seconds
        }
        result = []
        for alert in alerts:
            key = f"{alert.client}:{alert.domain}:{alert.analyzer}"
            if key not in self._dedup_cache:
                self._dedup_cache[key] = now
                result.append(alert)
        return result

    @staticmethod
    def _matches_at_label_boundary(domain: str, pattern: str) -> bool:
        domain_lower = domain.lower()
        pattern_lower = pattern.lower()
        labels = domain_lower.split(".")
        for label in labels:
            if label.startswith(pattern_lower):
                return True
        return False
