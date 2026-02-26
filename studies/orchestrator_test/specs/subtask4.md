# Subtask 4: LLM Classifier + Threat Intelligence

Implement two-tier LLM classification, domain sanitization, VirusTotal client, and threat feed manager for the `agentmon` DNS anomaly detection system.

## File Structure

Put `# path/to/file.py` as the first line in each code block. Produce these files:

- `agentmon/llm/__init__.py` (empty)
- `agentmon/llm/classifier.py`
- `agentmon/threat_feeds.py`
- `agentmon/threat_intel/__init__.py` (empty)
- `agentmon/threat_intel/virustotal.py`

## Module: `agentmon/llm/classifier.py`

### `DomainCategory` (enum.Enum)
Must have at least these members: BENIGN, SUSPICIOUS, LIKELY_MALICIOUS, DGA, UNKNOWN, ADVERTISING, TRACKING, CDN, CLOUD_PROVIDER, API_SERVICE.
Values should be lowercase strings matching the name (e.g. `BENIGN = "benign"`).

### `ClassificationResult` (dataclass)
- `domain`: str
- `category`: DomainCategory
- `confidence`: float
- `reasoning`: str
- `escalated`: bool = False
- `triage_category`: str | None = None

### `LLMConfig` (dataclass)
- `triage_model`: str
- `escalation_model`: str
- `host`: str = "http://localhost:11434"
- `escalation_threshold`: float = 0.7

### `sanitize_domain_for_prompt(domain: str) -> str`
Free function. Removes control characters (anything with ord < 32), newlines, and null bytes. Truncates to max 253 characters. Returns cleaned string.

### `DomainClassifier`
- `__init__(self, config: LLMConfig)`: stores config, creates empty cache dict and internal state
- Internal cache: dict[str, ClassificationResult] — 24h TTL

#### `async _call_ollama(self, **kwargs) -> dict`
Makes HTTP request to Ollama chat API. This method exists so tests can mock it. In production it would call `{config.host}/api/chat`. Just define the method signature — tests will mock it.

#### `async _unload_model(self, model: str)`
Unloads model from Ollama. Tests will mock this too.

#### `async classify(self, domain: str) -> ClassificationResult`
Two-tier classification:
1. Check cache — if domain is cached, return cached result immediately (no _call_ollama)
2. Call _call_ollama with triage_model. Parse JSON response to get category, confidence, reasoning
3. If triage result is "suspicious" or confidence < escalation_threshold: call _call_ollama with escalation_model. Set `escalated=True`, `triage_category` to the triage category string
4. Build ClassificationResult, cache it, return it
5. Map category strings to DomainCategory enum (case-insensitive)

## Module: `agentmon/threat_feeds.py`

### `ThreatFeedManager`
- `__init__(self, cache_dir: str)`: stores cache_dir, initializes empty set of malicious domains

#### `_load_cache(self, file_path: str)`
Reads a feed cache file line by line. For each line:
- Skip comments (lines starting with #) and blank lines
- Extract domain from URL: parse the line as URL, get the hostname
- Skip bare IP addresses (hostname is all digits and dots)
- Add valid domains to internal malicious domain set

Use `urllib.parse.urlparse` to extract hostname from URL lines.

#### `get_malicious_domains(self) -> set[str]`
Returns the set of malicious domains.

#### `check_domain(self, domain: str) -> str | None`
Check if domain or any of its parent domains match the malicious set.
- Check exact match first: if domain in malicious set, return the domain
- Then check parent domains: for "sub.evil.com", check "evil.com", then "com"
- Return the matching domain string, or None if no match

## Module: `agentmon/threat_intel/virustotal.py`

### `VirusTotalReputation` (dataclass)
- Fields: `malicious` (int), `suspicious` (int), `undetected` (int), `harmless` (int)

#### `risk_score` (property) -> float
Formula: `(malicious * 1.0 + suspicious * 0.5) / total` where total = sum of all four fields. If total is 0, return 0.0.

#### `is_high_risk` (property) -> bool
Return True if malicious >= 3 or risk_score > 0.2

#### `summary(self) -> str`
Return a string that includes "{malicious} malicious" and "{suspicious} suspicious" somewhere in it.

### `VirusTotalClient`
- `__init__(self, api_key: str | None = None)`: stores api_key
- `available` (property) -> bool: returns True if api_key is not None and not empty string
