from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field

from agentmon.analyzers.entropy import looks_like_dga
from agentmon.models.events import Alert, DNSEvent, Severity
from agentmon.storage.db import EventStore

_DEFAULT_DEDUP_TTL = 300  # 5 minutes


@dataclass
class AnalyzerConfig:
    known_bad_patterns: list[str] = field(default_factory=list)
    allowlist: set[str] = field(default_factory=set)
    ignore_suffixes: list[str] = field(default_factory=list)
    learning_mode: bool = False
    llm_enabled: bool = False
    dedup_ttl: int = _DEFAULT_DEDUP_TTL


class DNSBaselineAnalyzer:
    def __init__(self, store: EventStore, config: AnalyzerConfig):
        self.store = store
        self.config = config
        self._dedup_cache: dict[str, float] = {}  # key -> expiry timestamp

    @staticmethod
    def _matches_at_label_boundary(domain: str, pattern: str) -> bool:
        domain_lower = domain.lower()
        pattern_lower = pattern.lower()

        # Check if pattern is at the start of the domain
        if domain_lower.startswith(pattern_lower):
            return True

        # Check if pattern appears right after a dot
        search_prefix = "." + pattern_lower
        if search_prefix in domain_lower:
            return True

        return False

    def _is_ignored(self, domain: str) -> bool:
        for suffix in self.config.ignore_suffixes:
            if domain.endswith(suffix):
                return True
        return False

    def _is_dedup(self, key: str) -> bool:
        now = time.time()
        if key in self._dedup_cache:
            if self._dedup_cache[key] > now:
                return True
            else:
                del self._dedup_cache[key]
        return False

    def _mark_dedup(self, key: str):
        self._dedup_cache[key] = time.time() + self.config.dedup_ttl

    def analyze_event(self, event: DNSEvent) -> list[Alert]:
        alerts: list[Alert] = []

        # Always update baseline
        self.store.update_domain_baseline(event.client, event.domain, event.timestamp)

        # Skip ignored suffixes
        if self._is_ignored(event.domain):
            return alerts

        # Skip allowlisted domains (but baseline was already updated)
        if event.domain in self.config.allowlist:
            return alerts

        # Check known-bad patterns
        for pattern in self.config.known_bad_patterns:
            if self._matches_at_label_boundary(event.domain, pattern):
                dedup_key = f"known_bad:{event.client}:{event.domain}:{pattern}"
                if not self._is_dedup(dedup_key):
                    self._mark_dedup(dedup_key)
                    alerts.append(
                        Alert(
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
                    )
                break  # Only one known-bad alert per event

        # Check DGA
        is_dga, reasons = looks_like_dga(event.domain)
        if is_dga:
            dedup_key = f"dga:{event.client}:{event.domain}"
            if not self._is_dedup(dedup_key):
                self._mark_dedup(dedup_key)
                alerts.append(
                    Alert(
                        id=str(uuid.uuid4()),
                        timestamp=event.timestamp,
                        severity=Severity.MEDIUM,
                        title="Possible DGA domain",
                        description=f"{event.domain} looks like DGA: {', '.join(reasons)}",
                        source_event_type="dns",
                        client=event.client,
                        domain=event.domain,
                        analyzer="dns_baseline",
                        confidence=0.7,
                    )
                )

        # Check if domain is new (first-seen detection)
        # The baseline was already updated above, so check count > 1 means previously known
        row = self.store.conn.execute(
            "SELECT query_count FROM domain_baseline WHERE client = ? AND domain = ?",
            [event.client, event.domain],
        ).fetchone()
        is_new = row is not None and row[0] == 1  # first time seeing it

        if is_new and not self.config.learning_mode:
            dedup_key = f"new_domain:{event.client}:{event.domain}"
            if not self._is_dedup(dedup_key):
                self._mark_dedup(dedup_key)
                alerts.append(
                    Alert(
                        id=str(uuid.uuid4()),
                        timestamp=event.timestamp,
                        severity=Severity.INFO,
                        title="New domain observed",
                        description=f"First-seen domain: {event.domain} from {event.client}",
                        source_event_type="dns",
                        client=event.client,
                        domain=event.domain,
                        analyzer="dns_baseline",
                        confidence=0.5,
                    )
                )

        return alerts
