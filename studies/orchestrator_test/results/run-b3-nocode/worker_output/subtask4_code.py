# agentmon/llm/classifier.py
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

import aiohttp


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
    triage_category: Optional[str] = None


@dataclass
class LLMConfig:
    triage_model: str
    escalation_model: str
    host: str = "http://localhost:11434"
    escalation_threshold: float = 0.7


def sanitize_domain_for_prompt(domain: str) -> str:
    """
    Clean a domain string for use in an LLM prompt.
    """
    # Remove control characters
    domain = re.sub(r"[\x00-\x1F\x7F]", "", domain)
    # Keep only allowed characters
    domain = re.sub(r"[^A-Za-z0-9._-]", "", domain)
    # Truncate to 253 chars
    return domain[:253]


class DomainClassifier:
    def __init__(self, config: LLMConfig):
        self.config = config
        self._cache: Dict[str, ClassificationResult] = {}
        self._session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()

    async def _call_ollama(self, model: str, prompt: str) -> dict:
        """
        Call the Ollama API. Returns the parsed JSON response.
        """
        await self._ensure_session()
        url = f"{self.config.host}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        async with self._session.post(url, json=payload) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data

    async def _unload_model(self, model: str) -> None:
        """
        Unload a model from Ollama. Not used in tests but provided for completeness.
        """
        await self._ensure_session()
        url = f"{self.config.host}/api/unload"
        payload = {"model": model}
        async with self._session.post(url, json=payload) as resp:
            resp.raise_for_status()

    async def classify(self, domain: str) -> ClassificationResult:
        """
        Classify a domain using the triage and escalation models.
        """
        # Check cache
        cached = self._cache.get(domain)
        if cached:
            return cached

        sanitized = sanitize_domain_for_prompt(domain)
        triage_prompt = f"Classify the domain '{sanitized}'. Provide category, confidence, and reasoning."
        triage_resp = await self._call_ollama(self.config.triage_model, triage_prompt)

        # Parse triage response
        triage_category_str = triage_resp.get("category", "unknown").lower()
        triage_category = DomainCategory(triage_category_str) if triage_category_str in DomainCategory._value2member_map_ else DomainCategory.UNKNOWN
        triage_confidence = float(triage_resp.get("confidence", 0.0))
        triage_reasoning = triage_resp.get("reasoning", "")

        result = ClassificationResult(
            domain=domain,
            category=triage_category,
            confidence=triage_confidence,
            reasoning=triage_reasoning,
        )

        # Determine if escalation is needed
        needs_escalation = (
            triage_category_str == DomainCategory.SUSPICIOUS.value
            or triage_confidence < self.config.escalation_threshold
        )

        if needs_escalation:
            escalation_prompt = f"Escalate the classification for domain '{sanitized}'. Provide category, confidence, and reasoning."
            escalation_resp = await self._call_ollama(self.config.escalation_model, escalation_prompt)

            escalated_category_str = escalation_resp.get("category", "unknown").lower()
            escalated_category = DomainCategory(escalated_category_str) if escalated_category_str in DomainCategory._value2member_map_ else DomainCategory.UNKNOWN
            escalated_confidence = float(escalation_resp.get("confidence", 0.0))
            escalated_reasoning = escalation_resp.get("reasoning", "")

            result.category = escalated_category
            result.confidence = escalated_confidence
            result.reasoning = escalated_reasoning
            result.escalated = True
            result.triage_category = triage_category_str

        # Cache and return
        self._cache[domain] = result
        return result

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None


# agentmon/threat_feeds.py
import os
import urllib.parse
from typing import Set


class ThreatFeedManager:
    IP_REGEX = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")

    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        self.malicious_domains: Set[str] = set()

    def _load_cache(self, feed_file: str) -> None:
        """
        Load a threat feed file into the internal set.
        """
        path = os.path.join(self.cache_dir, feed_file)
        if not os.path.isfile(path):
            return

        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Extract hostname from URL or use line directly
                parsed = urllib.parse.urlparse(line if "://" in line else f"http://{line}")
                hostname = parsed.hostname or line
                if not hostname:
                    continue
                if self.IP_REGEX.match(hostname):
                    continue
                self.malicious_domains.add(hostname.lower())

    def get_malicious_domains(self) -> Set[str]:
        return self.malicious_domains

    def check_domain(self, domain: str) -> str | None:
        """
        Return the matched malicious domain or None.
        """
        domain = domain.lower()
        if domain in self.malicious_domains:
            return domain

        parts = domain.split(".")
        # Walk up the domain hierarchy
        for i in range(1, len(parts)):
            parent = ".".join(parts[i:])
            if parent in self.malicious_domains:
                return parent
        return None


# agentmon/threat_intel/virustotal.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class VirusTotalReputation:
    malicious: int
    suspicious: int
    undetected: int
    harmless: int

    @property
    def risk_score(self) -> float:
        total = self.malicious + self.suspicious + self.undetected + self.harmless
        if total == 0:
            return 0.0
        return (self.malicious * 1.0 + self.suspicious * 0.5) / total

    @property
    def is_high_risk(self) -> bool:
        return self.malicious >= 3 or self.risk_score > 0.15

    def summary(self) -> str:
        return f"{self.malicious} malicious, {self.suspicious} suspicious"


class VirusTotalClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    @property
    def available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())
