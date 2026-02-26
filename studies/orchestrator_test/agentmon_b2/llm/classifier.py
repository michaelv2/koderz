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
    cache_ttl: int = 86400


def sanitize_domain_for_prompt(domain: str) -> str:
    clean = re.sub(r'[\x00-\x1f\x7f]', "", domain)
    clean = clean.replace("\n", "").replace("\r", "")
    if len(clean) > 253:
        clean = clean[:253]
    return clean


class DomainClassifier:
    def __init__(self, config: LLMConfig):
        self.config = config
        self._cache: Dict[str, tuple[ClassificationResult, float]] = {}

    async def _call_ollama(self, **kwargs) -> Dict[str, Any]:
        model = kwargs.get("model", "")
        prompt = kwargs.get("prompt", "")
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
        pass

    async def classify(self, domain: str) -> ClassificationResult:
        cached = self._cache.get(domain)
        if cached:
            result, ts = cached
            if time.time() - ts < self.config.cache_ttl:
                return result

        clean_domain = sanitize_domain_for_prompt(domain)

        triage_prompt = (
            f"Classify this domain: {clean_domain}. "
            "Return JSON with category, confidence, reasoning."
        )
        triage_resp = await self._call_ollama(model=self.config.triage_model, prompt=triage_prompt)
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

        esc_prompt = (
            f"Deep analysis of domain: {clean_domain}. "
            f"Triage said: {triage_category}. "
            "Return JSON with category, confidence, reasoning."
        )
        esc_resp = await self._call_ollama(model=self.config.escalation_model, prompt=esc_prompt)
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
