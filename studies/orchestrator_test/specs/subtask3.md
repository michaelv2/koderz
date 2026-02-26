# Subtask 3: Detection Engine

Implement Shannon entropy calculation, DGA detection, known-bad pattern matching, and DNS baseline analysis for the `agentmon` system.

## File Structure

Put `# path/to/file.py` as the first line in each code block. Produce these files:

- `agentmon/analyzers/__init__.py` (empty)
- `agentmon/analyzers/entropy.py`
- `agentmon/analyzers/dns_baseline.py`

## Existing Modules (do NOT rewrite)

- `agentmon/models/events.py`: `DNSEvent` (frozen dataclass), `Alert`, `Severity` enum
- `agentmon/storage/db.py`: `EventStore` with `update_domain_baseline()`, `is_domain_known()`

## Module: `agentmon/analyzers/entropy.py`

### `calculate_entropy(s: str) -> float`
Shannon entropy of string s. For empty string return 0.0.
Formula: H = -sum(p * log2(p)) for each unique character frequency p.

### `calculate_domain_entropy(domain: str) -> float`
Strip common TLDs before calculating entropy. Remove the last label if it's a common TLD like com, net, org, io, etc. Then compute `calculate_entropy()` on the remaining string (joined without dots).

### `is_high_entropy_domain(domain: str) -> tuple[bool, float]`
Returns (flagged, entropy_value).
- Calculate domain entropy using `calculate_domain_entropy(domain)`
- Short domains (the part before TLD has fewer than 6 characters): never flag, return (False, entropy)
- Threshold: flag if entropy > 3.5
- Return (True, entropy) or (False, entropy)

### `has_excessive_consonants(domain: str) -> bool`
Check if the domain name (before TLD) has a high ratio of consonants.
- Strip TLD (last label after final dot)
- Remove non-alpha characters (hyphens, dots, digits)
- Count consonants (all letters that are NOT a, e, i, o, u)
- Return True if consonant ratio > 0.7 AND string length >= 6

### `looks_like_dga(domain: str) -> tuple[bool, list[str]]`
Multi-signal DGA detection. Returns (is_dga, list_of_reasons).

Check these signals:
1. High entropy (use `is_high_entropy_domain`) → reason: "high_entropy"
2. Excessive consonants (use `has_excessive_consonants`) → reason: "excessive_consonants"
3. Long alphanumeric subdomain (the part before TLD is >15 chars and mostly alphanumeric) → reason: "long_alphanumeric"
4. Alternating consonant-vowel-consonant pattern anomalies or no vowels in a long string → reason: "no_vowels" or "alternating_pattern"

**Critical rule**: DGA requires AT LEAST 2 signals. A single signal alone must NOT trigger is_dga=True.
- If len(reasons) >= 2: return (True, reasons)
- Otherwise: return (False, reasons)

## Module: `agentmon/analyzers/dns_baseline.py`

### `AnalyzerConfig` (dataclass)
- `known_bad_patterns`: list[str] = field(default_factory=list)
- `allowlist`: set[str] = field(default_factory=set)
- `ignore_suffixes`: list[str] = field(default_factory=list) — e.g. [".local", ".lan", ".arpa"]
- `learning_mode`: bool = False
- `llm_enabled`: bool = False
- `entropy_threshold`: float = 3.5

### `DNSBaselineAnalyzer`
- `__init__(self, store: EventStore, config: AnalyzerConfig)`
- Internal dedup cache: dict mapping (client, domain, analyzer_name) → last_alert_timestamp. TTL ~300 seconds.

### `analyze_event(self, event: DNSEvent) -> list[Alert]`
Main analysis method. Steps:

1. **Always update baseline**: call `store.update_domain_baseline(event.client, event.domain, event.timestamp)` — even for allowlisted domains

2. **Skip ignored suffixes**: if domain ends with any suffix in config.ignore_suffixes, return []

3. **Skip allowlisted**: if domain is in config.allowlist, return [] (but baseline was already updated in step 1)

4. **Check known-bad patterns**: for each pattern in config.known_bad_patterns, call `_matches_at_label_boundary(domain, pattern)`. If any match, create Alert with severity=HIGH, confidence=0.95, analyzer="known_bad_pattern". Check dedup before adding.

5. **Check DGA**: call `looks_like_dga(domain)`. If is_dga, create Alert with severity=MEDIUM, analyzer="dga_detection". Check dedup.

6. **Check new domain** (detection mode only): if NOT learning_mode and `not store.is_domain_known(client, domain)`, create Alert with severity=INFO, analyzer="new_domain". Check dedup.

7. Return collected alerts.

### `_matches_at_label_boundary(domain: str, pattern: str) -> bool` (staticmethod)
**Critical**: The pattern must match at a label boundary — either at the start of the domain or immediately after a dot.

- Case-insensitive comparison
- Split domain into labels by "."
- For each label, check if the label starts with the pattern (case-insensitive)
- This means "c2-" matches "c2-server.evil.com" (label "c2-server" starts with "c2-")
- But "c2-" does NOT match "ec2-35-169-254-100.compute-1.amazonaws.com" (label "ec2-35..." starts with "ec2-", not "c2-")

### Alert Deduplication
When creating an alert, check the dedup cache. Key = (client, domain, analyzer). If the same key was alerted within the last 300 seconds, suppress (don't add to alerts list). Otherwise, add to cache with current timestamp.
