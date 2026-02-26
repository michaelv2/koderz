import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Set

from agentmon.models.events import DNSEvent, Alert, Severity
from agentmon.storage.db import EventStore
from agentmon.analyzers.entropy import looks_like_dga


@dataclass
class AnalyzerConfig:
    known_bad_patterns: List[str] = field(default_factory=list)
    allowlist: Set[str] = field(default_factory=set)
    ignore_suffixes: List[str] = field(default_factory=list)
    learning_mode: bool = False
    llm_enabled: bool = False
    entropy_threshold: float = 3.5


class DNSBaselineAnalyzer:
    DEDUP_WINDOW = 300  # seconds

    def __init__(self, store: EventStore, config: AnalyzerConfig):
        self.store = store
        self.config = config
        self._dedup_cache: Dict[str, float] = {}  # domain -> last alert monotonic time

    @staticmethod
    def _matches_at_label_boundary(domain: str, pattern: str) -> bool:
        pattern_lower = pattern.lower()
        for label in domain.lower().split("."):
            if label.startswith(pattern_lower):
                return True
        return False

    def analyze_event(self, event: DNSEvent) -> List[Alert]:
        alerts: List[Alert] = []
        domain = event.domain
        client = event.client
        timestamp = event.timestamp

        # Check baseline existence BEFORE updating
        was_known = self.store.is_domain_known(client, domain)

        # Always update baseline (even for allowlisted domains)
        self.store.update_domain_baseline(client, domain, timestamp)

        # Skip alerting if domain matches any ignore suffix
        if any(domain.lower().endswith(suffix.lower()) for suffix in self.config.ignore_suffixes):
            return alerts

        # Skip alerting if domain is in the allowlist
        if domain.lower() in {d.lower() for d in self.config.allowlist}:
            return alerts

        # Check deduplication first
        now = time.monotonic()
        last_alert_time = self._dedup_cache.get(domain)
        if last_alert_time is not None and (now - last_alert_time) < self.DEDUP_WINDOW:
            return []

        # Known-bad patterns
        for pattern in self.config.known_bad_patterns:
            if self._matches_at_label_boundary(domain, pattern):
                alerts.append(
                    Alert(
                        id=str(uuid.uuid4()),
                        timestamp=timestamp,
                        severity=Severity.HIGH,
                        title="Known bad pattern detected",
                        description=f"Pattern '{pattern}' matched in domain '{domain}'.",
                        source_event_type="dns",
                        client=client,
                        domain=domain,
                        analyzer="dns_baseline",
                        confidence=0.9,
                    )
                )
                break

        # DGA detection
        is_dga, reasons = looks_like_dga(domain)
        if is_dga:
            alerts.append(
                Alert(
                    id=str(uuid.uuid4()),
                    timestamp=timestamp,
                    severity=Severity.MEDIUM,
                    title="Possible DGA domain detected",
                    description=f"DGA signals fired: {', '.join(reasons)}.",
                    source_event_type="dns",
                    client=client,
                    domain=domain,
                    analyzer="dns_baseline",
                    confidence=0.7,
                )
            )

        # New domain detection (only in detection mode)
        if not was_known and not self.config.learning_mode:
            alerts.append(
                Alert(
                    id=str(uuid.uuid4()),
                    timestamp=timestamp,
                    severity=Severity.INFO,
                    title="New domain observed",
                    description=f"Domain '{domain}' not seen before for client '{client}'.",
                    source_event_type="dns",
                    client=client,
                    domain=domain,
                    analyzer="dns_baseline",
                    confidence=0.5,
                )
            )

        # Update dedup cache if any alerts were generated
        if alerts:
            self._dedup_cache[domain] = now

        return alerts
