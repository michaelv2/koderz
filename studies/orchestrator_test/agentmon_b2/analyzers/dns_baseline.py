import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import List, Tuple

from agentmon.models.events import DNSEvent, Alert, Severity
from agentmon.storage.db import EventStore
from agentmon.analyzers.entropy import looks_like_dga


@dataclass
class AnalyzerConfig:
    known_bad_patterns: list[str] = field(default_factory=list)
    allowlist: set[str] = field(default_factory=set)
    ignore_suffixes: list[str] = field(default_factory=list)
    learning_mode: bool = True
    llm_enabled: bool = False
    entropy_threshold: float = 3.5


class DNSBaselineAnalyzer:
    def __init__(self, store: EventStore, config: AnalyzerConfig):
        self.store = store
        self.config = config
        self._dedup_cache: dict[Tuple[str, str], datetime] = {}
        self._dedup_ttl = 300

    @staticmethod
    def _matches_at_label_boundary(domain: str, pattern: str) -> bool:
        domain_lower = domain.lower()
        pattern_lower = pattern.lower()

        if domain_lower.startswith(pattern_lower):
            return True

        idx = 0
        while True:
            idx = domain_lower.find(".", idx)
            if idx == -1:
                break
            idx += 1
            if domain_lower[idx:].startswith(pattern_lower):
                return True

        return False

    def _is_deduplicated(self, client: str, domain: str) -> bool:
        key = (client, domain)
        if key in self._dedup_cache:
            elapsed = (datetime.now(timezone.utc) - self._dedup_cache[key]).total_seconds()
            if elapsed < self._dedup_ttl:
                return True
        return False

    def _mark_deduplicated(self, client: str, domain: str):
        self._dedup_cache[(client, domain)] = datetime.now(timezone.utc)

    def analyze_event(self, event: DNSEvent) -> List[Alert]:
        alerts: List[Alert] = []

        # Always update baseline
        self.store.update_domain_baseline(event.client, event.domain, event.timestamp)

        # Ignore suffixes
        for suffix in self.config.ignore_suffixes:
            if event.domain.endswith(suffix):
                return alerts

        # Allowlist
        if event.domain in self.config.allowlist:
            return alerts

        # Deduplication
        if self._is_deduplicated(event.client, event.domain):
            return alerts

        # Known-bad patterns
        for pattern in self.config.known_bad_patterns:
            if self._matches_at_label_boundary(event.domain, pattern):
                alert = Alert(
                    id=str(uuid.uuid4()),
                    timestamp=event.timestamp,
                    severity=Severity.HIGH,
                    title=f"Known-bad pattern: {pattern}",
                    description=f"{event.domain} matches known-bad pattern '{pattern}'",
                    source_event_type="dns",
                    client=event.client,
                    domain=event.domain,
                    analyzer="dns_baseline",
                    confidence=0.95,
                )
                alerts.append(alert)
                self._mark_deduplicated(event.client, event.domain)
                return alerts

        # DGA detection
        is_dga, reasons = looks_like_dga(event.domain)
        if is_dga:
            alert = Alert(
                id=str(uuid.uuid4()),
                timestamp=event.timestamp,
                severity=Severity.MEDIUM,
                title="Possible DGA domain",
                description=f"{event.domain}: {', '.join(reasons)}",
                source_event_type="dns",
                client=event.client,
                domain=event.domain,
                analyzer="dns_baseline",
                confidence=0.7,
            )
            alerts.append(alert)
            self._mark_deduplicated(event.client, event.domain)
            return alerts

        # New domain detection
        row = self.store.conn.execute(
            "SELECT query_count FROM domain_baseline WHERE client = ? AND domain = ?",
            (event.client, event.domain),
        ).fetchone()
        is_first_seen = row is not None and row[0] == 1

        if is_first_seen and not self.config.learning_mode:
            alert = Alert(
                id=str(uuid.uuid4()),
                timestamp=event.timestamp,
                severity=Severity.INFO,
                title="New domain observed",
                description=f"First time seeing {event.domain} from {event.client}",
                source_event_type="dns",
                client=event.client,
                domain=event.domain,
                analyzer="dns_baseline",
                confidence=0.3,
            )
            alerts.append(alert)
            self._mark_deduplicated(event.client, event.domain)

        return alerts
