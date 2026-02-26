# Subtask 3: Detection Engine

Implement TWO Python files for entropy/DGA detection and DNS baseline analysis.

## File 1: `agentmon/analyzers/entropy.py`

### `calculate_entropy(s: str) -> float`
Shannon entropy of a string. Returns 0.0 for empty string or single-char repeated.
```python
import math
from collections import Counter

def calculate_entropy(s: str) -> float:
    if not s:
        return 0.0
    length = len(s)
    counts = Counter(s)
    entropy = 0.0
    for count in counts.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy
```

### `calculate_domain_entropy(domain: str) -> float`
Strip common TLDs before computing entropy. Remove the last label (TLD like .com, .net, .org) and dots, then compute entropy of remaining string.
```python
def calculate_domain_entropy(domain: str) -> float:
    parts = domain.split(".")
    if len(parts) >= 2:
        # Remove TLD (last part)
        name_part = ".".join(parts[:-1])
    else:
        name_part = domain
    # Remove dots for entropy calculation
    name_part = name_part.replace(".", "")
    return calculate_entropy(name_part)
```

### `is_high_entropy_domain(domain: str, threshold: float = 3.5) -> tuple[bool, float]`
Returns (is_flagged, entropy_value). Short domains (name part < 6 chars before TLD) are never flagged.
```python
def is_high_entropy_domain(domain: str, threshold: float = 3.5) -> tuple[bool, float]:
    parts = domain.split(".")
    if len(parts) >= 2:
        name_part = ".".join(parts[:-1]).replace(".", "")
    else:
        name_part = domain
    
    if len(name_part) < 6:
        return False, calculate_domain_entropy(domain)
    
    entropy = calculate_domain_entropy(domain)
    return entropy > threshold, entropy
```

### `has_excessive_consonants(domain: str) -> bool`
Check if domain has excessive consonant ratio (>0.7 of non-dot alpha chars are consonants).
```python
def has_excessive_consonants(domain: str) -> bool:
    vowels = set("aeiouAEIOU")
    parts = domain.split(".")
    if len(parts) >= 2:
        name = ".".join(parts[:-1])
    else:
        name = domain
    name = name.replace(".", "").replace("-", "")
    alpha_chars = [c for c in name if c.isalpha()]
    if len(alpha_chars) < 5:
        return False
    consonants = [c for c in alpha_chars if c not in vowels]
    ratio = len(consonants) / len(alpha_chars)
    return ratio > 0.7
```

### `looks_like_dga(domain: str) -> tuple[bool, list[str]]`
Multi-signal DGA detection. Returns (is_dga, list_of_reasons). Must require AT LEAST 2 signals to flag as DGA.

Signals to check:
1. High entropy (>3.5 on name part)
2. Excessive consonant ratio (>0.7)
3. Long alphanumeric segments (>10 chars without hyphens/dots that mix letters and digits)
4. Alternating letter-digit pattern
5. No vowels in name part (when name part is >5 chars)

```python
def looks_like_dga(domain: str) -> tuple[bool, list[str]]:
    reasons = []
    parts = domain.split(".")
    if len(parts) >= 2:
        name_part = ".".join(parts[:-1]).replace(".", "")
    else:
        name_part = domain
    
    # Signal 1: high entropy
    flagged, entropy = is_high_entropy_domain(domain)
    if flagged:
        reasons.append(f"high_entropy ({entropy:.2f})")
    
    # Signal 2: excessive consonants
    if has_excessive_consonants(domain):
        reasons.append("excessive_consonants")
    
    # Signal 3: long alphanumeric segment with mixed letters and digits
    segments = name_part.split("-")
    for seg in segments:
        if len(seg) > 10:
            has_alpha = any(c.isalpha() for c in seg)
            has_digit = any(c.isdigit() for c in seg)
            if has_alpha and has_digit:
                reasons.append("long_mixed_alphanumeric")
                break
    
    # Signal 4: alternating letter-digit pattern (at least 4 alternations)
    if len(name_part) >= 8:
        alternations = 0
        for i in range(1, len(name_part)):
            if name_part[i-1].isalpha() != name_part[i].isalpha() and name_part[i-1].isalnum() and name_part[i].isalnum():
                alternations += 1
        if alternations >= 4:
            reasons.append("alternating_pattern")
    
    # Signal 5: no vowels (when long enough)
    vowels = set("aeiouAEIOU")
    if len(name_part) > 5 and not any(c in vowels for c in name_part):
        reasons.append("no_vowels")
    
    is_dga = len(reasons) >= 2
    return is_dga, reasons
```

**TEST REQUIREMENTS**:
- `calculate_entropy("")` == 0.0
- `calculate_entropy("aaaa")` == 0.0
- `abs(calculate_entropy("ab") - 1.0) < 0.01`
- `calculate_entropy("k8xp2m9qr7w4zt1v") > 3.0`
- `calculate_domain_entropy("google.com")` < 3.0 (strips .com, computes entropy of "google")
- `is_high_entropy_domain("google.com")` -> (False, _)
- `is_high_entropy_domain("xk9p2mq7rw4zt1vbn.com")` -> (True, entropy > 3.5)
- `is_high_entropy_domain("xk9.com")` -> (False, _) (too short)
- `has_excessive_consonants("xkcd-mngmnt-prblm.com")` -> True
- `has_excessive_consonants("facebook.com")` -> False
- `looks_like_dga("google.com")` -> (False, _)
- `looks_like_dga("api.github.com")` -> (False, _)
- `looks_like_dga("cdn.cloudflare.net")` -> (False, _)
- `looks_like_dga("xk9p2mq7rw4zt1vbn3cx.com")` -> (True, reasons with len >= 2)
- If `looks_like_dga` returns True, reasons must have >= 2 items
- `looks_like_dga("abcdefghijklmno.com")` -> if True, must have >= 2 reasons

## File 2: `agentmon/analyzers/dns_baseline.py`

### `AnalyzerConfig` dataclass
```python
from dataclasses import dataclass, field

@dataclass
class AnalyzerConfig:
    known_bad_patterns: list[str] = field(default_factory=list)
    allowlist: set[str] = field(default_factory=set)
    ignore_suffixes: list[str] = field(default_factory=list)
    learning_mode: bool = True
    llm_enabled: bool = False
    entropy_threshold: float = 3.5
```

### `DNSBaselineAnalyzer` class
```python
import uuid
from datetime import datetime, timezone
from agentmon.models.events import DNSEvent, Alert, Severity
from agentmon.storage.db import EventStore
from agentmon.analyzers.entropy import looks_like_dga


class DNSBaselineAnalyzer:
    def __init__(self, store: EventStore, config: AnalyzerConfig):
        self.store = store
        self.config = config
        self._dedup_cache = {}  # {(client, domain): last_alert_time}
        self._dedup_ttl = 300  # 5 minutes

    @staticmethod
    def _matches_at_label_boundary(domain: str, pattern: str) -> bool:
        """Check if pattern appears at a label boundary in the domain.
        
        Label boundaries are: start of domain, or immediately after a dot.
        
        CRITICAL: "c2-" in "ec2-35-169-254-100.compute-1.amazonaws.com" must NOT match
        because "c2-" appears mid-label (inside "ec2-").
        
        "c2-" in "c2-server.evil.com" DOES match (start of domain).
        "c2-" in "sub.c2-server.evil.com" DOES match (after dot).
        
        Case-insensitive.
        """
        domain_lower = domain.lower()
        pattern_lower = pattern.lower()
        
        # Check at start of domain
        if domain_lower.startswith(pattern_lower):
            return True
        
        # Check after each dot
        idx = 0
        while True:
            idx = domain_lower.find(".", idx)
            if idx == -1:
                break
            idx += 1  # move past the dot
            if domain_lower[idx:].startswith(pattern_lower):
                return True
        
        return False

    def _is_deduplicated(self, client: str, domain: str) -> bool:
        """Check if we recently alerted on this client+domain."""
        key = (client, domain)
        if key in self._dedup_cache:
            elapsed = (datetime.now(timezone.utc) - self._dedup_cache[key]).total_seconds()
            if elapsed < self._dedup_ttl:
                return True
        return False

    def _mark_deduplicated(self, client: str, domain: str):
        self._dedup_cache[(client, domain)] = datetime.now(timezone.utc)

    def analyze_event(self, event: DNSEvent) -> list[Alert]:
        """Analyze a DNS event and return list of alerts.
        
        Always update baseline first (even for allowlisted domains).
        
        Then check:
        1. Ignore suffixes (.local, .lan, .arpa) -> skip alerting
        2. Allowlist -> skip alerting
        3. Deduplication -> skip if recently alerted for same client+domain
        4. Known-bad patterns -> HIGH alert (confidence >= 0.9)
        5. DGA detection -> MEDIUM alert
        6. New domain (not in baseline, detection mode only) -> INFO alert
        
        In learning_mode: suppress new-domain INFO alerts, but still alert on known-bad and DGA.
        """
        alerts = []
        
        # Always update baseline
        self.store.update_domain_baseline(event.client, event.domain, event.timestamp)
        
        # Check ignored suffixes
        for suffix in self.config.ignore_suffixes:
            if event.domain.endswith(suffix):
                return alerts
        
        # Check allowlist
        if event.domain in self.config.allowlist:
            return alerts
        
        # Check deduplication
        if self._is_deduplicated(event.client, event.domain):
            return alerts
        
        # Check known-bad patterns
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
        
        # Check DGA
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
        
        # New domain detection (only in detection mode, not learning mode)
        # Check if domain was already known BEFORE we updated baseline
        # Since we already updated, query_count > 1 means it was known before
        row = self.store.conn.execute(
            "SELECT query_count FROM domain_baseline WHERE client = ? AND domain = ?",
            (event.client, event.domain)
        ).fetchone()
        is_first_seen = row and row[0] == 1
        
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
```

**CRITICAL TEST REQUIREMENTS**:

For `_matches_at_label_boundary`:
- `_matches_at_label_boundary("c2-server.evil.com", "c2-")` -> True (start of domain)
- `_matches_at_label_boundary("sub.c2-server.evil.com", "c2-")` -> True (after dot)
- `_matches_at_label_boundary("ec2-35-169-254-100.compute-1.amazonaws.com", "c2-")` -> **FALSE** (mid-label!)
- `_matches_at_label_boundary("ec2-54-234-89-123.us-east-1.compute.amazonaws.com", "c2-")` -> **FALSE**
- `_matches_at_label_boundary("C2-Server.Evil.com", "c2-")` -> True (case-insensitive)
- `_matches_at_label_boundary("integrate-api.service.com", "rat-")` -> **FALSE** ("rat-" is inside "integrate-")

For `analyze_event`:
- Known-bad "c2-server.evil.com" -> HIGH alert, confidence >= 0.9
- Allowlisted "safe.example.com" -> no alerts
- Ignored suffix "printer.local" -> no alerts
- New domain in detection mode -> INFO alert
- Learning mode: no INFO alerts on new domains, but baseline still updated
- Learning mode: still alerts HIGH on known-bad patterns
- DGA domain "xk9p2mq7rw4zt1vbn3cx.com" -> MEDIUM or LOW alert
- Deduplication: second analyze_event on same domain -> 0 alerts (or fewer than first)
- Baseline always updated even for allowlisted domains

Write COMPLETE, RUNNABLE code for both files. No stubs. Wrap each in ```python blocks with filename comment.
