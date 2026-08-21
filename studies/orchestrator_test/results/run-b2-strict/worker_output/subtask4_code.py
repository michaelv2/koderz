# agentmon/llm/classifier.py
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

import httpx


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


@dataclass
class ClassificationResult:
    domain: str
    category: DomainCategory
    confidence: float
    reasoning: str
    escalated: bool = False
    triage_category: str = ""


@dataclass
class LLMConfig:
    triage_model: str = "llama3.2:3b"
    escalation_model: str = "llama3.3:70b"
    ollama_host: str = "http://localhost:11434"
    escalation_threshold: float = 0.7
    cache_ttl: int = 86400  # 24 hours


def sanitize_domain_for_prompt(domain: str) -> str:
    """Strip control chars, newlines, and truncate to 253 chars max."""
    # Remove control characters (0x00-0x1F, 0x7F)
    clean = re.sub(r'[\x00-\x1f\x7f]', "", domain)
    # Remove newlines explicitly
    clean = clean.replace("\n", "").replace("\r", "")
    # Truncate to DNS max length
    if len(clean) > 253:
        clean = clean[:253]
    return clean


class DomainClassifier:
    def __init__(self, config: LLMConfig):
        self.config = config
        self._cache: Dict[str, tuple[ClassificationResult, float]] = {}

    async def _call_ollama(self, model: str, prompt: str) -> Dict[str, Any]:
        """Call Ollama chat API. To be mocked in tests."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.config.ollama_host}/api/chat",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def _unload_model(self, model: str) -> None:
        """Unload model from Ollama. To be mocked in tests."""
        # Real implementation would call the Ollama API to unload the model.
        pass

    async def classify(self, domain: str) -> ClassificationResult:
        """Two-tier classification: triage first, then escalation if needed."""
        # Check cache
        cached = self._cache.get(domain)
        if cached:
            result, ts = cached
            if time.time() - ts < self.config.cache_ttl:
                return result

        clean_domain = sanitize_domain_for_prompt(domain)

        # Triage
        triage_prompt = (
            f"Classify this domain: {clean_domain}. "
            "Return JSON with category, confidence, reasoning."
        )
        triage_resp = await self._call_ollama(self.config.triage_model, triage_prompt)
        triage_data = json.loads(triage_resp["message"]["content"])

        triage_category = triage_data.get("category", "unknown").lower()
        triage_confidence = float(triage_data.get("confidence", 0.5))
        triage_reasoning = triage_data.get("reasoning", "")

        needs_escalation = (
            triage_category in ("suspicious", "unknown")
            or triage_confidence < self.config.escalation_threshold
        )

        if not needs_escalation:
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
        esc_prompt = (
            f"Deep analysis of domain: {clean_domain}. "
            f"Triage said: {triage_category}. "
            "Return JSON with category, confidence, reasoning."
        )
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


# agentmon/threat_feeds/__init__.py
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
from typing import Set


class ThreatFeedManager:
    def __init__(self, cache_dir: str = "/tmp/agentmon_feeds"):
        self.cache_dir = Path(cache_dir)
        self._domains: Set[str] = set()

    def _load_cache(self, file_path: str | Path) -> None:
        """Load domains from a feed cache file.
        Each line is either a URL or a comment (starting with #) or empty.
        Extract hostname from URLs. Skip bare IP addresses (no dots-separated hostname).
        Skip lines starting with # and empty lines.
        """
        path = Path(file_path)
        if not path.is_file():
            return
        with path.open() as f:
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
                    # Ignore malformed lines
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

    def get_malicious_domains(self) -> Set[str]:
        """Return all known malicious domains."""
        return set(self._domains)

    def check_domain(self, domain: str) -> Dict | None:
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


# agentmon/threat_intel/virustotal.py
from __future__ import annotations

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


class VirusTotalClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    @property
    def available(self) -> bool:
        """Client is available only if API key is set."""
        return bool(self.api_key and len(self.api_key) > 0)
