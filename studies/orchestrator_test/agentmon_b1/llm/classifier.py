from __future__ import annotations

import enum
import json
import re
import time
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any


class DomainCategory(enum.Enum):
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
    triage_model: str = "llama3.2:3b"
    escalation_model: str = "llama3.3:70b"
    ollama_host: str = "http://localhost:11434"
    escalation_threshold: float = 0.7
    cache_ttl: int = 86400


def sanitize_domain_for_prompt(domain: str) -> str:
    cleaned = re.sub(r'[\x00-\x1f\n\r\t]', '', domain)
    cleaned = re.sub(r'[^A-Za-z0-9.\-_]', '', cleaned)
    return cleaned[:253]


def _parse_category(cat_str: str) -> DomainCategory:
    try:
        return DomainCategory(cat_str.lower())
    except ValueError:
        return DomainCategory.UNKNOWN


class DomainClassifier:
    def __init__(self, config: LLMConfig):
        self.config = config
        self._cache: Dict[str, tuple[ClassificationResult, float]] = {}

    async def _call_ollama(self, **kwargs) -> dict:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.config.ollama_host}/api/chat",
                json=kwargs,
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()

    async def _unload_model(self, model: str) -> None:
        pass

    async def classify(self, domain: str) -> ClassificationResult:
        cached = self._cache.get(domain)
        if cached:
            result, expiry = cached
            if expiry > time.time():
                return result

        triage_prompt = (
            f"Classify the following domain as JSON with fields: "
            f"category, confidence, reasoning.\nDomain: {sanitize_domain_for_prompt(domain)}"
        )
        triage_resp = await self._call_ollama(
            model=self.config.triage_model,
            messages=[{"role": "user", "content": triage_prompt}],
            stream=False,
        )
        triage_content = triage_resp.get("message", {}).get("content", "")
        triage_data = self._parse_json_from_content(triage_content)
        triage_category_str = triage_data.get("category", "unknown")
        triage_category = _parse_category(triage_category_str)
        triage_confidence = float(triage_data.get("confidence", 0.0))
        triage_reasoning = triage_data.get("reasoning", "")

        escalated = False
        final_category = triage_category
        final_confidence = triage_confidence
        final_reasoning = triage_reasoning

        if triage_category_str.lower() == "suspicious" or triage_confidence < self.config.escalation_threshold:
            escalation_prompt = (
                f"Given the domain {sanitize_domain_for_prompt(domain)} and the triage "
                f"category '{triage_category_str}', provide a detailed analysis and "
                f"final classification as JSON with fields: category, confidence, reasoning."
            )
            escalation_resp = await self._call_ollama(
                model=self.config.escalation_model,
                messages=[{"role": "user", "content": escalation_prompt}],
                stream=False,
            )
            escalation_content = escalation_resp.get("message", {}).get("content", "")
            escalation_data = self._parse_json_from_content(escalation_content)
            final_category = _parse_category(escalation_data.get("category", "unknown"))
            final_confidence = float(escalation_data.get("confidence", 0.0))
            final_reasoning = escalation_data.get("reasoning", "")
            escalated = True

        result = ClassificationResult(
            domain=domain,
            category=final_category,
            confidence=final_confidence,
            reasoning=final_reasoning,
            escalated=escalated,
            triage_category=triage_category_str,
        )

        expiry = time.time() + self.config.cache_ttl
        self._cache[domain] = (result, expiry)

        return result

    @staticmethod
    def _parse_json_from_content(content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            m = re.search(r'\{.*\}', content, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except json.JSONDecodeError:
                    pass
            return {"category": "unknown", "confidence": 0.0, "reasoning": "Failed to parse"}
