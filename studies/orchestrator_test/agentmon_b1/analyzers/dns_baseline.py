from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import List, Set

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
    dedup_ttl: int = 300


class DNSBaselineAnalyzer:
    def __init__(self, store: EventStore, config: AnalyzerConfig):
        self.store = store
        self.config = config
        self._dedup_cache: dict[str, float] = {}

    @staticmethod
    def _matches_at_label_boundary(domain: str, pattern: str) -> bool:
        domain_lc = domain.lower()
        pattern_lc = pattern.lower()
        for label in domain_lc.split("."):
            if label.startswith(pattern_lc):
                return True
        return False

    def _is_dedup(self, key: str) -> bool:
        now = time.time()
        expired_keys = [k for k, exp in self._dedup_cache.items() if exp <= now]
        for k in expired_keys:
            del self._dedup_cache[k]
        return key in self._dedup_cache

    def _mark_dedup(self, key: str) -> None:
        self._dedup_cache[key] = time.time() + self.config.dedup_ttl

    def _is_ignored(self, domain: str) -> bool:
        domain_lc = domain.lower()
        for suffix in self.config.ignore_suffixes:
            if domain_lc.endswith(suffix.lower()):
                return True
        return False

    def analyze_event(self, event: DNSEvent) -> List[Alert]:
        alerts: List[Alert] = []

        was_known = self.store.is_domain_known(event.client, event.domain)

        self.store.update_domain_baseline(event.client, event.domain, event.timestamp)

        if event.domain in self.config.allowlist:
            return alerts

        if self._is_ignored(event.domain):
            return alerts

        for pattern in self.config.known_bad_patterns:
            if self._matches_at_label_boundary(event.domain, pattern):
                dedup_key = f"known_bad:{event.client}:{event.domain}"
                if not self._is_dedup(dedup_key):
                    self._mark_dedup(dedup_key)
                    alerts.append(Alert(
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
                    ))
                break

        is_dga, reasons = looks_like_dga(event.domain)
        if is_dga:
            dedup_key = f"dga:{event.client}:{event.domain}"
            if not self._is_dedup(dedup_key):
                self._mark_dedup(dedup_key)
                alerts.append(Alert(
                    id=str(uuid.uuid4()),
                    timestamp=event.timestamp,
                    severity=Severity.MEDIUM,
                    title="Possible DGA domain",
                    description=f"{event.domain} shows DGA signals: {', '.join(reasons)}",
                    source_event_type="dns",
                    client=event.client,
                    domain=event.domain,
                    analyzer="dga_detector",
                    confidence=0.7,
                ))

        if not was_known and not self.config.learning_mode:
            dedup_key = f"new_domain:{event.client}:{event.domain}"
            if not self._is_dedup(dedup_key):
                self._mark_dedup(dedup_key)
                alerts.append(Alert(
                    id=str(uuid.uuid4()),
                    timestamp=event.timestamp,
                    severity=Severity.INFO,
                    title=f"New domain: {event.domain}",
                    description=f"First time seeing {event.domain} from {event.client}",
                    source_event_type="dns",
                    client=event.client,
                    domain=event.domain,
                    analyzer="dns_baseline",
                    confidence=0.5,
                ))

        return alerts
