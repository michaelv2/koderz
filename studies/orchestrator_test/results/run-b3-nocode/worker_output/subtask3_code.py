# agentmon/analyzers/entropy.py
import math
import re
from collections import Counter
from typing import List, Tuple

VOWELS = set("aeiouAEIOU")


def calculate_entropy(s: str) -> float:
    """Return the Shannon entropy of a string."""
    if not s:
        return 0.0
    freq = Counter(s)
    length = len(s)
    entropy = -sum((count / length) * math.log2(count / length) for count in freq.values())
    return entropy


def calculate_domain_entropy(domain: str) -> float:
    """
    Calculate entropy of a domain after stripping the last label (TLD).
    For single-label domains, use the whole string.
    """
    parts = domain.split(".")
    if len(parts) > 1:
        domain_without_tld = ".".join(parts[:-1])
    else:
        domain_without_tld = domain
    return calculate_entropy(domain_without_tld)


def is_high_entropy_domain(domain: str) -> Tuple[bool, float]:
    """
    Flag a domain if the pre-TLD part is longer than 6 characters and its entropy > 3.5.
    Returns a tuple of (flagged, entropy_value).
    """
    parts = domain.split(".")
    if len(parts) > 1:
        pre_tld = ".".join(parts[:-1])
    else:
        pre_tld = domain
    entropy = calculate_entropy(pre_tld)
    flagged = len(pre_tld) > 6 and entropy > 3.5
    return flagged, entropy


def has_excessive_consonants(domain: str) -> bool:
    """
    Return True if the pre-TLD part has a consonant-to-total ratio > 0.7 and length > 6.
    """
    parts = domain.split(".")
    if len(parts) > 1:
        pre_tld = ".".join(parts[:-1])
    else:
        pre_tld = domain
    if len(pre_tld) <= 6:
        return False
    consonants = sum(1 for c in pre_tld if c.isalpha() and c not in VOWELS)
    total_letters = sum(1 for c in pre_tld if c.isalpha())
    if total_letters == 0:
        return False
    ratio = consonants / total_letters
    return ratio > 0.7


def _alternating_transition_count(label: str) -> int:
    """Count transitions between letter and digit in a label."""
    if not label:
        return 0
    prev_is_digit = label[0].isdigit()
    transitions = 0
    for ch in label[1:]:
        is_digit = ch.isdigit()
        if is_digit != prev_is_digit:
            transitions += 1
            prev_is_digit = is_digit
    return transitions


def looks_like_dga(domain: str) -> Tuple[bool, List[str]]:
    """
    Multi-signal DGA detection.
    Returns (is_dga, reasons) where reasons is a list of fired signal names.
    """
    reasons = []

    # 1. High entropy
    parts = domain.split(".")
    if len(parts) > 1:
        pre_tld = ".".join(parts[:-1])
    else:
        pre_tld = domain
    if calculate_entropy(pre_tld) > 3.5:
        reasons.append("high_entropy")

    # 2. Excessive consonant ratio
    if has_excessive_consonants(domain):
        reasons.append("excessive_consonants")

    # 3. Long alphanumeric label (>15 chars, only alphanum)
    for label in parts:
        if len(label) > 15 and label.isalnum():
            reasons.append("long_alphanumeric_label")
            break

    # 4. Alternating letters and digits (many transitions)
    for label in parts:
        if _alternating_transition_count(label) > 5:
            reasons.append("alternating_letters_digits")
            break

    # 5. No vowels in long labels (>5 chars)
    for label in parts:
        if len(label) > 5 and not any(ch in VOWELS for ch in label):
            reasons.append("no_vowels_in_long_label")
            break

    is_dga = len(reasons) >= 2
    return is_dga, reasons


# agentmon/analyzers/dns_baseline.py
import uuid
from dataclasses import dataclass, field
from typing import List, Dict

from agentmon.models.events import DNSEvent, Alert, Severity
from agentmon.storage.db import EventStore
from agentmon.analyzers.entropy import looks_like_dga


@dataclass
class AnalyzerConfig:
    known_bad_patterns: List[str] = field(default_factory=list)
    allowlist: set = field(default_factory=set)
    ignore_suffixes: List[str] = field(default_factory=list)
    learning_mode: bool = False
    llm_enabled: bool = False
    entropy_threshold: float = 3.5


class DNSBaselineAnalyzer:
    DEDUP_WINDOW = 300  # seconds

    def __init__(self, store: EventStore, config: AnalyzerConfig):
        self.store = store
        self.config = config
        self.dedup_cache: Dict[str, float] = {}  # domain -> last alert timestamp

    @staticmethod
    def _matches_at_label_boundary(domain: str, pattern: str) -> bool:
        """
        Pattern must appear at the start of the domain or immediately after a dot.
        Case-insensitive.
        """
        pattern_lower = pattern.lower()
        for label in domain.split("."):
            if label.lower().startswith(pattern_lower):
                return True
        return False

    def analyze_event(self, event: DNSEvent) -> List[Alert]:
        alerts: List[Alert] = []

        domain = event.domain
        client = event.client
        timestamp = event.timestamp

        # 1. Check baseline existence before updating
        existed_before = self.store.has_domain(domain, client)

        # 1. Update baseline
        self.store.update_domain_baseline(domain, client)

        # 2. Skip if domain ends with any ignore suffix
        if any(domain.lower().endswith(suffix.lower()) for suffix in self.config.ignore_suffixes):
            return alerts

        # 3. Skip if domain is allowlisted
        if domain.lower() in {d.lower() for d in self.config.allowlist}:
            return alerts

        # 4. Known bad patterns
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
                # If a known bad pattern is found, we don't need to check other signals
                break

        # 5. DGA detection
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

        # 6. New domain detection
        if not existed_before and not self.config.learning_mode:
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

        # 7. Deduplication
        last_alert_ts = self.dedup_cache.get(domain)
        if last_alert_ts is not None and (timestamp - last_alert_ts).total_seconds() < self.DEDUP_WINDOW:
            # Suppress duplicate alerts
            alerts = []

        # Update dedup cache if any alerts were generated
        if alerts:
            self.dedup_cache[domain] = timestamp

        return alerts
