# Subtask 3: Detection Engine

Implement two files for a DNS anomaly detection system's analysis layer.

## File 1: `agentmon/analyzers/entropy.py`

### calculate_entropy(s: str) -> float
Shannon entropy of a string. Empty string returns 0.0. Formula: -sum(p * log2(p)) for each character frequency p.

### calculate_domain_entropy(domain: str) -> float
Calculate entropy of a domain after stripping the TLD. For "google.com" → entropy of "google". For "sub.example.co.uk" → entropy of "sub.example.co" (strip only last label). For single-label domains, return entropy of the whole string.

### is_high_entropy_domain(domain: str) -> tuple[bool, float]
Returns (flagged, entropy_value). A domain is flagged if:
- The part before the TLD has length > 6 (short domains are never flagged)
- AND entropy exceeds 3.5
Normal domains like "google.com" must NOT be flagged.

### has_excessive_consonants(domain: str) -> bool
Returns True if the domain (before TLD) has an excessive consonant-to-vowel ratio. Vowels = "aeiou". Consider the domain label(s) before the TLD. If consonant ratio > 0.7 and label length > 6, return True. "facebook.com" → False. "xkcd-mngmnt-prblm.com" → True.

### looks_like_dga(domain: str) -> tuple[bool, list[str]]
Multi-signal DGA detection. Check these signals:
1. High entropy (>3.5 for the pre-TLD part)
2. Excessive consonant ratio (from has_excessive_consonants)
3. Long alphanumeric label (>15 chars of continuous alphanum in a single label, no hyphens or dots)
4. Alternating letters and digits (many transitions between letters and digits)
5. No vowels in long labels (>5 chars with no vowels)

Return (is_dga, reasons). DGA is flagged ONLY if 2 or more signals fire. reasons is a list of signal names that fired.
Normal domains like "google.com", "api.github.com", "cdn.cloudflare.net" must NOT be flagged.

## File 2: `agentmon/analyzers/dns_baseline.py`

### AnalyzerConfig (dataclass)
- Fields: `known_bad_patterns` (list[str], default_factory=list), `allowlist` (set[str], default_factory=set), `ignore_suffixes` (list[str], default_factory=list), `learning_mode` (bool, default=False), `llm_enabled` (bool, default=False), `entropy_threshold` (float, default=3.5)

### DNSBaselineAnalyzer
- Constructor: `__init__(self, store: EventStore, config: AnalyzerConfig)`
  - store is an agentmon.storage.db.EventStore instance
  - Initialize a deduplication cache (dict mapping domain→timestamp of last alert)

- `@staticmethod _matches_at_label_boundary(domain: str, pattern: str) -> bool`
  Label-boundary matching — the pattern must appear either at the very start of the domain OR immediately after a "." character. Case-insensitive.
  - "c2-server.evil.com" with pattern "c2-" → True (starts at domain beginning)
  - "sub.c2-server.evil.com" with pattern "c2-" → True (starts after a dot)
  - "ec2-35-169-254-100.compute-1.amazonaws.com" with pattern "c2-" → False (the "c2-" is mid-label, part of "ec2-")
  - "C2-Server.Evil.com" with pattern "c2-" → True (case-insensitive)
  - "integrate-api.service.com" with pattern "rat-" → False ("rat-" in "integrate" is mid-label)

- `analyze_event(event: DNSEvent) -> list[Alert]`
  Analyze a DNS event and return a list of alerts. Steps:
  1. Always update the domain baseline in the store (even for allowlisted domains)
  2. Skip alerting if domain matches any ignore_suffix (e.g., ".local", ".lan", ".arpa")
  3. Skip alerting if domain is in the allowlist
  4. Check known-bad patterns using _matches_at_label_boundary. If match: HIGH severity alert, confidence >= 0.9
  5. Check DGA using looks_like_dga from entropy module. If DGA: MEDIUM severity alert
  6. In detection mode (not learning_mode): if domain not in baseline for this client → INFO alert
  7. In learning mode: suppress new-domain INFO alerts, but still alert on known-bad and DGA
  8. Deduplication: if the same domain was alerted within the dedup window (e.g., 300 seconds), suppress duplicate alerts. The second call to analyze_event for the same domain should return fewer or zero alerts.

  Each alert needs: id (uuid), timestamp (from event), severity, title, description, source_event_type="dns", client, domain, analyzer="dns_baseline", confidence

Import from `agentmon.models.events`: DNSEvent, Alert, Severity
Import from `agentmon.storage.db`: EventStore
Import from `agentmon.analyzers.entropy`: looks_like_dga

Write ONLY these two files. Output them as two separate fenced code blocks, each preceded by a comment with the file path.
