# Subtask 4: LLM Classifier + Threat Intelligence

Implement THREE Python files.

## File 1: `agentmon/llm/classifier.py`

### `DomainCategory` enum
```python
from enum import Enum

class DomainCategory(str, Enum):
    BENIGN = "benign"
    SUSPICIOUS = "suspicious"
    LIKELY_MALICIOUS = "likely_malicious"
    DGA = "dga"
    UNKNOWN = "unknown"
    ADVERTISING = "advertising"
    TRACKING = "tracking"
    CDN = "cdn"
    CLOUD_PROVIDER = "cloud_provider"
    API_SERVICE = "api_service"
```

### `ClassificationResult` dataclass
```python
from dataclasses import dataclass

@dataclass
class ClassificationResult:
    domain: str
    category: DomainCategory
    confidence: float
    reasoning: str
    escalated: bool = False
    triage_category: str = ""
```

### `LLMConfig` dataclass
```python
@dataclass
class LLMConfig:
    triage_model: str = "llama3.2:3b"
    escalation_model: str = "llama3.3:70b"
    ollama_host: str = "http://localhost:11434"
    escalation_threshold: float = 0.7
    cache_ttl: int = 86400  # 24 hours
```

### `sanitize_domain_for_prompt(domain: str) -> str`
```python
import re

def sanitize_domain_for_prompt(domain: str) -> str:
    """Strip control chars, newlines, and truncate to 253 chars max."""
    # Remove control characters (0x00-0x1F, 0x7F)
    clean = re.sub(r'[\x00-\x1f\x7f]', '', domain)
    # Remove newlines explicitly
    clean = clean.replace('\n', '').replace('\r', '')
    # Truncate to DNS max length
    if len(clean) > 253:
        clean = clean[:253]
    return clean
```

### `DomainClassifier` class
```python
import json
import time

class DomainClassifier:
    def __init__(self, config: LLMConfig):
        self.config = config
        self._cache = {}  # {domain: (result, timestamp)}

    async def _call_ollama(self, model: str, prompt: str) -> dict:
        """Call Ollama chat API. To be mocked in tests."""
        # Real implementation would use httpx
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.config.ollama_host}/api/chat",
                json={"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False},
                timeout=60.0,
            )
            return resp.json()

    async def _unload_model(self, model: str):
        """Unload model from Ollama. To be mocked in tests."""
        pass

    async def classify(self, domain: str) -> ClassificationResult:
        """Two-tier classification: triage first, escalate if suspicious.
        
        1. Check cache first
        2. Call triage model
        3. If triage says suspicious/unknown (confidence < escalation_threshold), call escalation model
        4. Cache result
        """
        # Check cache
        if domain in self._cache:
            result, ts = self._cache[domain]
            if time.time() - ts < self.config.cache_ttl:
                return result
        
        clean_domain = sanitize_domain_for_prompt(domain)
        
        # Triage
        triage_prompt = f"Classify this domain: {clean_domain}. Return JSON with category, confidence, reasoning."
        triage_resp = await self._call_ollama(self.config.triage_model, triage_prompt)
        triage_data = json.loads(triage_resp["message"]["content"])
        
        triage_category = triage_data.get("category", "unknown").lower()
        triage_confidence = float(triage_data.get("confidence", 0.5))
        triage_reasoning = triage_data.get("reasoning", "")
        
        # Determine if escalation needed
        needs_escalation = triage_category in ("suspicious", "unknown") or triage_confidence < self.config.escalation_threshold
        
        if not needs_escalation:
            # Map category string to enum
            try:
                cat = DomainCategory(triage_category)
            except ValueError:
                cat = DomainCategory.UNKNOWN
            
            result = ClassificationResult(
                domain=domain,
                category=cat,
                confidence=triage_confidence,
                reasoning=triage_reasoning,
                escalated=False,
                triage_category=triage_category,
            )
            self._cache[domain] = (result, time.time())
            await self._unload_model(self.config.triage_model)
            return result
        
        # Escalation
        esc_prompt = f"Deep analysis of domain: {clean_domain}. Triage said: {triage_category}. Return JSON with category, confidence, reasoning."
        esc_resp = await self._call_ollama(self.config.escalation_model, esc_prompt)
        esc_data = json.loads(esc_resp["message"]["content"])
        
        esc_category = esc_data.get("category", "unknown").lower()
        esc_confidence = float(esc_data.get("confidence", 0.5))
        esc_reasoning = esc_data.get("reasoning", "")
        
        try:
            cat = DomainCategory(esc_category)
        except ValueError:
            cat = DomainCategory.UNKNOWN
        
        result = ClassificationResult(
            domain=domain,
            category=cat,
            confidence=esc_confidence,
            reasoning=esc_reasoning,
            escalated=True,
            triage_category=triage_category,
        )
        self._cache[domain] = (result, time.time())
        await self._unload_model(self.config.escalation_model)
        return result
```

**TEST REQUIREMENTS for classifier**:
- ClassificationResult has fields: domain, category, confidence, reasoning, escalated (default False)
- DomainCategory enum has: BENIGN, SUSPICIOUS, LIKELY_MALICIOUS, DGA, UNKNOWN, ADVERTISING, TRACKING, CDN, CLOUD_PROVIDER, API_SERVICE
- sanitize_domain_for_prompt: removes \x00, \n chars; truncates to <= 253 chars
- Two-tier flow: triage returns suspicious -> escalation called -> result has escalated=True, triage_category set
- Benign triage -> no escalation, escalated=False
- Cache: second classify of same domain does NOT call _call_ollama again (call_count stays at 1)

## File 2: `agentmon/threat_feeds/__init__.py`

### `ThreatFeedManager` class
```python
from urllib.parse import urlparse

class ThreatFeedManager:
    def __init__(self, cache_dir: str = "/tmp/agentmon_feeds"):
        self.cache_dir = cache_dir
        self._domains = set()

    def _load_cache(self, file_path: str):
        """Load domains from a feed cache file.
        
        Each line is either a URL or a comment (starting with #) or empty.
        Extract hostname from URLs. Skip bare IP addresses (no dots-separated hostname).
        Skip lines starting with # and empty lines.
        """
        with open(file_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    parsed = urlparse(line)
                    hostname = parsed.hostname
                    if hostname and not self._is_ip(hostname):
                        self._domains.add(hostname)
                except Exception:
                    pass

    @staticmethod
    def _is_ip(s: str) -> bool:
        """Check if string is an IP address."""
        parts = s.split(".")
        if len(parts) == 4:
            try:
                return all(0 <= int(p) <= 255 for p in parts)
            except ValueError:
                return False
        return False

    def get_malicious_domains(self) -> set[str]:
        """Return all known malicious domains."""
        return self._domains

    def check_domain(self, domain: str) -> dict | None:
        """Check if domain or any parent domain is in threat feeds.
        
        Returns dict with feed info if found, None if clean.
        Check exact match first, then check parent domains.
        e.g., for "sub.evil.com" check: "sub.evil.com", "evil.com"
        """
        # Exact match
        if domain in self._domains:
            return {"domain": domain, "source": "threat_feed", "match_type": "exact"}
        
        # Check parent domains
        parts = domain.split(".")
        for i in range(1, len(parts)):
            parent = ".".join(parts[i:])
            if parent in self._domains:
                return {"domain": parent, "source": "threat_feed", "match_type": "parent"}
        
        return None
```

**TEST REQUIREMENTS for ThreatFeedManager**:
- _load_cache parses URLs, extracts hostnames, skips comments/empty/IPs
- get_malicious_domains returns set of domains
- check_domain: exact match returns non-None
- check_domain: subdomain of malicious domain returns non-None (parent match)
- check_domain: clean domain returns None

## File 3: `agentmon/threat_intel/virustotal.py`

### `VirusTotalReputation` dataclass
```python
from dataclasses import dataclass

@dataclass
class VirusTotalReputation:
    malicious: int
    suspicious: int
    undetected: int
    harmless: int

    @property
    def risk_score(self) -> float:
        """risk = (malicious * 1.0 + suspicious * 0.5) / total"""
        total = self.malicious + self.suspicious + self.undetected + self.harmless
        if total == 0:
            return 0.0
        return (self.malicious * 1.0 + self.suspicious * 0.5) / total

    @property
    def is_high_risk(self) -> bool:
        """High risk if malicious >= 3 or risk_score > 0.2"""
        return self.malicious >= 3 or self.risk_score > 0.2

    def summary(self) -> str:
        """Return string like '3 malicious, 1 suspicious out of N engines'"""
        total = self.malicious + self.suspicious + self.undetected + self.harmless
        return f"{self.malicious} malicious, {self.suspicious} suspicious out of {total} engines"
```

### `VirusTotalClient` class
```python
class VirusTotalClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    @property
    def available(self) -> bool:
        """Client is available only if API key is set."""
        return self.api_key is not None and len(self.api_key) > 0
```

**TEST REQUIREMENTS for VirusTotal**:
- VirusTotalReputation(5, 2, 10, 50).risk_score ≈ 6.0/67 ≈ 0.0896
- VirusTotalReputation(5, 0, 5, 10).is_high_risk is True
- summary includes "3 malicious" and "1 suspicious"
- VirusTotalClient(api_key=None).available is False

Write COMPLETE, RUNNABLE code for all three files. Wrap each in ```python blocks with filename comment.
