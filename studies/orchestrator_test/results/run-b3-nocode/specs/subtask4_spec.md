# Subtask 4: LLM Classifier + Threat Intelligence

Implement three files for a DNS anomaly detection system.

## File 1: `agentmon/llm/classifier.py`

### DomainCategory (enum.Enum)
Values (string): BENIGN="benign", SUSPICIOUS="suspicious", LIKELY_MALICIOUS="likely_malicious", DGA="dga", UNKNOWN="unknown", ADVERTISING="advertising", TRACKING="tracking", CDN="cdn", CLOUD_PROVIDER="cloud_provider", API_SERVICE="api_service"

### ClassificationResult (dataclass)
- Fields: `domain` (str), `category` (DomainCategory), `confidence` (float), `reasoning` (str), `escalated` (bool, default=False), `triage_category` (str or None, default=None)

### LLMConfig (dataclass)
- Fields: `triage_model` (str), `escalation_model` (str), `host` (str, default="http://localhost:11434"), `escalation_threshold` (float, default=0.7)

### sanitize_domain_for_prompt(domain: str) -> str
- Strip control characters (anything with ord < 32, including \x00, \n, \r, \t)
- Strip any character that isn't alphanumeric, dot, hyphen, or underscore
- Truncate to max 253 characters
- Return the cleaned string

### DomainClassifier
- Constructor: `__init__(self, config: LLMConfig)` — stores config, initializes a cache dict (domain → ClassificationResult) and optional TTL
- `async _call_ollama(**kwargs) -> dict` — makes HTTP request to Ollama API. This will be mocked in tests.
- `async _unload_model(model: str) -> None` — sends unload request. This will be mocked in tests.
- `async classify(domain: str) -> ClassificationResult`:
  1. Check cache first. If domain is cached, return cached result immediately (no API call).
  2. Call _call_ollama for triage using triage_model. The response is JSON with keys: category, confidence, reasoning.
  3. Parse the JSON response. Map category string to DomainCategory enum.
  4. If triage category is "suspicious" or confidence < escalation_threshold: escalate by calling _call_ollama with escalation_model. Parse that response too. Set escalated=True, triage_category= the original triage category string.
  5. If triage is "benign" with high confidence: no escalation. Set escalated=False.
  6. Cache the result before returning.

## File 2: `agentmon/threat_feeds.py`

### ThreatFeedManager
- Constructor: `__init__(self, cache_dir: str)` — stores cache_dir, initializes empty set of malicious domains
- `_load_cache(feed_file: str)` — reads a text file line by line:
  - Skip lines starting with "#" and empty lines
  - For each URL line, extract the hostname (domain) from the URL using urllib.parse.urlparse
  - Skip bare IP addresses (lines where the hostname looks like an IP — all digits and dots)
  - Add extracted domains to the internal set
- `get_malicious_domains() -> set[str]` — returns the set of known malicious domains
- `check_domain(domain: str) -> str | None`:
  - Check exact match first: if domain is in the malicious set, return the domain
  - Check parent domains: for "sub.evil.com", check "evil.com" too. Walk up the domain labels.
  - If no match found, return None

## File 3: `agentmon/threat_intel/virustotal.py`

### VirusTotalReputation (dataclass)
- Fields: `malicious` (int), `suspicious` (int), `undetected` (int), `harmless` (int)
- Property `risk_score` -> float: `(malicious * 1.0 + suspicious * 0.5) / total` where total = malicious + suspicious + undetected + harmless. If total is 0, return 0.0.
- Property `is_high_risk` -> bool: True if malicious >= 3 OR risk_score > 0.15
- Method `summary() -> str`: return a string containing "{malicious} malicious" and "{suspicious} suspicious" (exact format flexible, but must contain those substrings)

### VirusTotalClient
- Constructor: `__init__(self, api_key: str | None = None)` — stores api_key
- Property `available` -> bool: returns True if api_key is not None and not empty

Write ONLY these three files. Output them as three separate fenced code blocks, each preceded by a comment with the file path.
