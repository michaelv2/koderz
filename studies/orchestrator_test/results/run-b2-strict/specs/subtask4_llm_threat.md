# Subtask 4: LLM Classifier + Threat Intelligence

Implement THREE Python files. Output them as THREE separate fenced code blocks, clearly labeled with file paths.

## File 1: `agentmon/llm/classifier.py`

### Imports
```python
from __future__ import annotations
import enum
import json
import re
import time
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
```

### `DomainCategory` (enum.Enum)
Values (strings): BENIGN="benign", SUSPICIOUS="suspicious", LIKELY_MALICIOUS="likely_malicious", DGA="dga", UNKNOWN="unknown", ADVERTISING="advertising", TRACKING="tracking", CDN="cdn", CLOUD_PROVIDER="cloud_provider", API_SERVICE="api_service"

### `ClassificationResult` dataclass
Fields:
- `domain`: str
- `category`: DomainCategory
- `confidence`: float
- `reasoning`: str
- `escalated`: bool = False
- `triage_category`: Optional[str] = None

### `LLMConfig` dataclass
Fields:
- `triage_model`: str = "llama3.2:3b"
- `escalation_model`: str = "llama3.3:70b"
- `ollama_host`: str = "http://localhost:11434"
- `escalation_threshold`: float = 0.7
- `cache_ttl`: int = 86400

### `sanitize_domain_for_prompt(domain: str) -> str` (module-level function)
- Remove control characters (chars < 0x20) and newlines
- Remove any chars that aren't alphanumeric, dot, hyphen, or underscore
- Truncate to 253 characters max
- Return cleaned string

### `DomainClassifier` class

Constructor: `__init__(self, config: LLMConfig)`
- `self.config = config`
- `self._cache: Dict[str, tuple[ClassificationResult, float]] = {}` (domain -> (result, expiry_timestamp))

#### `async _call_ollama(self, **kwargs) -> dict`
This is an async method that calls the Ollama API. It will be mocked in tests.
Implementation: Use httpx or urllib to POST to `{config.ollama_host}/api/chat` with the kwargs.
For tests, this method is patched, so the actual implementation just needs to exist.

Simple stub implementation:
```python
async def _call_ollama(self, **kwargs) -> dict:
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{self.config.ollama_host}/api/chat",
            json=kwargs,
            timeout=60,
        )
        return resp.json()
```

#### `async _unload_model(self, model: str) -> None`
Stub that does nothing (will be mocked in tests):
```python
async def _unload_model(self, model: str) -> None:
    pass
```

#### `async classify(self, domain: str) -> ClassificationResult`
Two-tier classification flow:

1. **Check cache**: If domain in _cache and not expired, return cached result
2. **Triage** (Tier 1):
   - Call `_call_ollama(model=config.triage_model, messages=[...], stream=False)`
   - The prompt asks to classify the domain as JSON with fields: category, confidence, reasoning
   - Parse the JSON response from `result["message"]["content"]`
   - Map category string to DomainCategory enum (case-insensitive, default UNKNOWN)
3. **Decide escalation**: If triage category is "suspicious" or confidence < config.escalation_threshold:
   - Call `_call_ollama(model=config.escalation_model, messages=[...], stream=False)`
   - Parse escalation response
   - Create ClassificationResult with escalated=True, triage_category=triage_category_str
4. **No escalation**: Create ClassificationResult with escalated=False
5. **Cache the result** with expiry = time.time() + config.cache_ttl
6. Return result

When parsing JSON from model response, handle potential errors gracefully:
```python
try:
    data = json.loads(content)
except json.JSONDecodeError:
    # Try to extract JSON from markdown code blocks
    m = re.search(r'\{.*\}', content, re.DOTALL)
    if m:
        data = json.loads(m.group())
    else:
        data = {"category": "unknown", "confidence": 0.0, "reasoning": "Failed to parse"}
```

Map category string to enum:
```python
def _parse_category(cat_str: str) -> DomainCategory:
    try:
        return DomainCategory(cat_str.lower())
    except ValueError:
        return DomainCategory.UNKNOWN
```

## File 2: `agentmon/threat_intel/virustotal.py`

### Imports
```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
```

### `VirusTotalReputation` dataclass
Fields:
- `malicious`: int
- `suspicious`: int
- `undetected`: int
- `harmless`: int

Properties:
- `risk_score` -> float: `(malicious * 1.0 + suspicious * 0.5) / total` where total = malicious + suspicious + undetected + harmless. If total == 0, return 0.0
- `is_high_risk` -> bool: True if malicious >= 5 OR risk_score > 0.2

Methods:
- `summary() -> str`: Return string like "3 malicious, 1 suspicious, 5 undetected, 20 harmless"

### `VirusTotalClient` class
Constructor: `__init__(self, api_key: Optional[str] = None)`
- `self._api_key = api_key`

Property:
- `available` -> bool: Return True if api_key is not None and not empty

Method:
- `async check_domain(self, domain: str) -> Optional[VirusTotalReputation]`: If not available, return None. Otherwise call VT API (will be mocked in tests). Stub is fine.

## File 3: `agentmon/threat_feeds/__init__.py`

### Imports
```python
from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Set
from urllib.parse import urlparse
```

### `_is_ip(host: str) -> bool` (module-level)
Check if host is an IP address. Use regex: `r'^\d{1,3}(\.\d{1,3}){3}$'`

### `ThreatFeedManager` class

Constructor: `__init__(self, cache_dir: str = "/tmp/agentmon_feeds")`
- `self.cache_dir = cache_dir`
- `self._domains: Set[str] = set()`

#### `get_malicious_domains(self) -> Set[str]`
Return copy of self._domains

#### `_load_cache(self, feed_file: str)`
Read the feed file line by line:
- Skip empty lines and lines starting with "#"
- For each URL line, try to extract the domain:
  - Use `urlparse(line.strip())` to get hostname
  - If hostname and NOT an IP (use _is_ip), add to self._domains

#### `check_domain(self, domain: str) -> Optional[str]`
- Check exact match: if domain in self._domains, return the domain
- Check subdomain match: split domain parts, check parent domains
  - E.g., for "sub.evil.com", check "evil.com" and "sub.evil.com"
  - Walk through: for i in range(len(parts)):, join parts[i:] and check
- Return None if no match

#### `async update_feeds(self) -> None`
Stub — just pass (feeds are loaded from cache files).
