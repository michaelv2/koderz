# Subtask 3: Detection Engine

Implement TWO Python files. Output them as TWO separate fenced code blocks, clearly labeled.

## File 1: `agentmon/analyzers/entropy.py`

### Imports
```python
from __future__ import annotations
import math
import re
from typing import Tuple, List
```

### Constants
```python
_COMMON_TLDS = {"com", "net", "org", "io", "co", "uk", "de", "fr", "ru", "cn",
                "jp", "br", "au", "in", "it", "nl", "se", "no", "fi", "dk",
                "info", "biz", "us"}
_MIN_DOMAIN_LENGTH_FOR_ENTROPY = 6
_HIGH_ENTROPY_THRESHOLD = 3.5
_CONSONANT_RATIO_THRESHOLD = 0.75
```

### `calculate_entropy(s: str) -> float`
Shannon entropy of a string.
- If empty string, return 0.0
- Count frequency of each character
- entropy = -sum(p * log2(p)) for each character probability p
- Return the entropy value

### `calculate_domain_entropy(domain: str) -> float`
- Split domain by "."
- Strip known TLDs from the end (check if last label is in _COMMON_TLDS, if so remove it)
- Join remaining labels with "" (no separator) to get the domain body
- Return calculate_entropy of the domain body

### `is_high_entropy_domain(domain: str) -> Tuple[bool, float]`
- Calculate domain entropy using calculate_domain_entropy
- Get domain body (strip TLDs, join labels)
- If body length < _MIN_DOMAIN_LENGTH_FOR_ENTROPY: return (False, entropy)
- If entropy > _HIGH_ENTROPY_THRESHOLD: return (True, entropy)
- Otherwise: return (False, entropy)

### `has_excessive_consonants(domain: str) -> bool`
- Extract the domain body (strip TLD, join labels without dots)
- Remove non-alpha characters from body
- If body is empty, return False
- Count consonants (non-vowels, where vowels = "aeiouAEIOU")
- Consonant ratio = consonant_count / total_alpha_count
- Return ratio >= _CONSONANT_RATIO_THRESHOLD

### `looks_like_dga(domain: str) -> Tuple[bool, List[str]]`
Multi-signal DGA detection. Check ALL of these signals, collect reasons:

1. **High entropy**: Use is_high_entropy_domain. If True, add reason "high_entropy"

2. **Excessive consonants**: Use has_excessive_consonants. If True, add reason "excessive_consonants"

3. **Long alphanumeric run**: Get domain body (no TLD, no dots). Check if there's a run of 10+ alphanumeric chars without hyphens or other separators.
   - Regex: `r'[a-zA-Z0-9]{10,}'`
   - If match, add reason "long_alphanumeric_run"

4. **Alternating pattern**: Check if the domain body has an alternating consonant-vowel-consonant pattern for 8+ consecutive characters. Use a simple approach: check for alternation.
   - Regex approach: look for patterns like `[bcdfghjklmnpqrstvwxyz][aeiou]` repeated 4+ times
   - If found, add reason "alternating_pattern"

5. **No vowels**: Get domain body (no TLD), check if it has zero vowels (only consonants/digits/hyphens) and length >= 6.
   - If no vowels in alpha chars and len >= 6, add reason "no_vowels"

CRITICAL: Require **2 or more** reasons to classify as DGA.
- If len(reasons) >= 2: return (True, reasons)
- Otherwise: return (False, reasons)

Example test cases that must work:
- "google.com" -> NOT DGA (low entropy, normal consonant ratio)
- "api.github.com" -> NOT DGA
- "cdn.cloudflare.net" -> NOT DGA
- "xk9p2mq7rw4zt1vbn3cx.com" -> IS DGA (high entropy + long alphanumeric + likely no vowels)
- "abcdefghijklmno.com" -> if DGA, must have >= 2 reasons

## File 2: `agentmon/analyzers/dns_baseline.py`

### Imports
```python
from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Set, Optional
from agentmon.models.events import DNSEvent, Alert, Severity
from agentmon.storage.db import EventStore
from agentmon.analyzers.entropy import looks_like_dga
```

### `AnalyzerConfig` dataclass
Fields:
- `known_bad_patterns`: List[str] = field(default_factory=list)
- `allowlist`: Set[str] = field(default_factory=set)
- `ignore_suffixes`: List[str] = field(default_factory=list)
- `learning_mode`: bool = False
- `llm_enabled`: bool = False
- `dedup_ttl`: int = 300  (seconds, 5 minutes)

### `DNSBaselineAnalyzer` class

Constructor: `__init__(self, store: EventStore, config: AnalyzerConfig)`
- `self.store = store`
- `self.config = config`
- `self._dedup_cache: dict[str, float] = {}`  (key -> expiry timestamp)

#### `@staticmethod _matches_at_label_boundary(domain: str, pattern: str) -> bool`
THIS IS CRITICAL AND SUBTLE. The pattern must match at the START of a domain label (component separated by dots).

Logic:
1. Lowercase both domain and pattern
2. Split domain into labels by "."
3. For each label, check if it STARTS WITH the pattern
4. Return True if any label starts with the pattern, False otherwise

Example:
- `_matches_at_label_boundary("c2-server.evil.com", "c2-")` -> True ("c2-server" starts with "c2-")
- `_matches_at_label_boundary("sub.c2-server.evil.com", "c2-")` -> True
- `_matches_at_label_boundary("ec2-35-169-254-100.compute-1.amazonaws.com", "c2-")` -> FALSE! ("ec2-35..." does NOT start with "c2-")
- `_matches_at_label_boundary("integrate-api.service.com", "rat-")` -> FALSE! ("integrate-api" does NOT start with "rat-")

This is a staticmethod that can be called as `DNSBaselineAnalyzer._matches_at_label_boundary(domain, pattern)`.

#### `_is_ignored(self, domain: str) -> bool`
Check if domain ends with any suffix in config.ignore_suffixes.

#### `_is_dedup(self, key: str) -> bool`
Check if key is in _dedup_cache AND the expiry time hasn't passed.
Clean expired entries too.

#### `_mark_dedup(self, key: str)`
Add key to _dedup_cache with expiry = current time + config.dedup_ttl

#### `analyze_event(self, event: DNSEvent) -> List[Alert]`
Main analysis pipeline:

1. **Always update baseline** first: `self.store.update_domain_baseline(event.client, event.domain, event.timestamp)`

2. Check allowlist: if domain in config.allowlist, return [] (no alerts)

3. Check ignored suffixes: if _is_ignored(domain), return []

4. Collect alerts:

   a. **Known-bad pattern check**: For each pattern in config.known_bad_patterns:
      - If `_matches_at_label_boundary(event.domain, pattern)`:
      - Dedup key = f"known_bad:{event.client}:{event.domain}"
      - If not deduped: create Alert with severity=HIGH, confidence=0.95, analyzer="dns_baseline", title like "Known-bad pattern: {pattern}", mark_dedup
      - Break after first match

   b. **DGA check**: Call `looks_like_dga(event.domain)`
      - If is_dga: dedup key = f"dga:{event.client}:{event.domain}"
      - If not deduped: create Alert with severity=MEDIUM, confidence=0.7, analyzer="dga_detector"

   c. **First-seen / new domain check**:
      - Query `self.store.is_domain_known(event.client, event.domain)` — but note: we already called update_domain_baseline above, so the domain IS now known. The trick: check if the domain was known BEFORE this event.
      - APPROACH: Check query_count. After the update, if query_count == 1, it's a first-seen domain.
      - Alternative simpler approach: check is_domain_known BEFORE the update. Move the baseline update to the end, or check differently.

      ACTUALLY — the simplest correct approach: Call `is_domain_known` BEFORE `update_domain_baseline`. Let me restructure:

      Step 1: Check if domain is known FIRST: `was_known = self.store.is_domain_known(event.client, event.domain)`
      Step 2: Update baseline: `self.store.update_domain_baseline(...)`
      Step 3: In alert generation, if NOT was_known and NOT learning_mode:
        - Dedup key = f"new_domain:{event.client}:{event.domain}"
        - If not deduped: create Alert with severity=INFO, confidence=0.5, analyzer="dns_baseline", title like "New domain: {domain}"

      In learning_mode: suppress new-domain alerts but still update baseline (which we already did).

5. Return collected alerts list.

**REVISED analyze_event flow:**
```
def analyze_event(self, event):
    alerts = []

    # Check if domain was known before this event
    was_known = self.store.is_domain_known(event.client, event.domain)

    # Always update baseline
    self.store.update_domain_baseline(event.client, event.domain, event.timestamp)

    # Skip alerts for allowlisted domains
    if event.domain in self.config.allowlist:
        return alerts

    # Skip ignored suffixes
    if self._is_ignored(event.domain):
        return alerts

    # 1. Known-bad patterns (always checked, even in learning mode)
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

    # 2. DGA detection (always checked, even in learning mode)
    is_dga, reasons = looks_like_dga(event.domain)
    if is_dga:
        dedup_key = f"dga:{event.client}:{event.domain}"
        if not self._is_dedup(dedup_key):
            self._mark_dedup(dedup_key)
            alerts.append(Alert(
                id=str(uuid.uuid4()),
                timestamp=event.timestamp,
                severity=Severity.MEDIUM,
                title=f"Possible DGA domain",
                description=f"{event.domain} shows DGA signals: {', '.join(reasons)}",
                source_event_type="dns",
                client=event.client,
                domain=event.domain,
                analyzer="dga_detector",
                confidence=0.7,
            ))

    # 3. New domain alert (suppressed in learning mode)
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
```
