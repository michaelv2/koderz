from __future__ import annotations

import enum
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Optional


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
    escalation_model: str = "llama3.1:8b"
    ollama_host: str = "http://localhost:11434"
    escalation_threshold: float = 0.8
    cache_ttl_seconds: float = 86400.0  # 24 hours


def sanitize_domain_for_prompt(domain: str) -> str:
    # Strip control characters and newlines
    clean = re.sub(r"[\x00-\x1f\x7f]", "", domain)
    # Remove any remaining newlines
    clean = clean.replace("\n", "").replace("\r", "")
    # Strip non-printable chars
    clean = "".join(c for c in clean if c.isprintable())
    # Truncate to DNS max length
    if len(clean) > 253:
        clean = clean[:253]
    return clean


_CATEGORY_MAP = {
    "benign": DomainCategory.BENIGN,
    "suspicious": DomainCategory.SUSPICIOUS,
    "likely_malicious": DomainCategory.LIKELY_MALICIOUS,
    "dga": DomainCategory.DGA,
    "unknown": DomainCategory.UNKNOWN,
    "advertising": DomainCategory.ADVERTISING,
    "tracking": DomainCategory.TRACKING,
    "cdn": DomainCategory.CDN,
    "cloud_provider": DomainCategory.CLOUD_PROVIDER,
    "api_service": DomainCategory.API_SERVICE,
}

_ESCALATION_CATEGORIES = {"suspicious", "unknown"}


class DomainClassifier:
    def __init__(self, config: LLMConfig):
        self.config = config
        self._cache: dict[str, tuple[ClassificationResult, float]] = {}

    async def classify(self, domain: str) -> ClassificationResult:
        # Check cache
        if domain in self._cache:
            result, ts = self._cache[domain]
            if time.monotonic() - ts < self.config.cache_ttl_seconds:
                return result

        clean_domain = sanitize_domain_for_prompt(domain)

        # Tier 1: Triage
        triage_result = await self._run_triage(clean_domain)
        triage_category = triage_result.get("category", "unknown").lower()
        triage_confidence = float(triage_result.get("confidence", 0.5))
        triage_reasoning = triage_result.get("reasoning", "")

        # Decide if escalation is needed
        if (
            triage_category in _ESCALATION_CATEGORIES
            or triage_confidence < self.config.escalation_threshold
        ):
            # Tier 2: Escalation
            esc_result = await self._run_escalation(clean_domain, triage_result)
            esc_category = esc_result.get("category", "unknown").lower()
            esc_confidence = float(esc_result.get("confidence", 0.5))
            esc_reasoning = esc_result.get("reasoning", "")

            category = _CATEGORY_MAP.get(esc_category, DomainCategory.UNKNOWN)
            result = ClassificationResult(
                domain=domain,
                category=category,
                confidence=esc_confidence,
                reasoning=esc_reasoning,
                escalated=True,
                triage_category=triage_category,
            )
        else:
            category = _CATEGORY_MAP.get(triage_category, DomainCategory.UNKNOWN)
            result = ClassificationResult(
                domain=domain,
                category=category,
                confidence=triage_confidence,
                reasoning=triage_reasoning,
                escalated=False,
                triage_category=triage_category,
            )

        # Unload models after classification
        await self._unload_model(self.config.triage_model)

        # Cache the result
        self._cache[domain] = (result, time.monotonic())

        return result

    async def _run_triage(self, domain: str) -> dict[str, Any]:
        prompt = (
            f"Classify the following domain as one of: benign, suspicious, "
            f"likely_malicious, dga, advertising, tracking, cdn, cloud_provider, "
            f"api_service, unknown.\n\nDomain: {domain}\n\n"
            f"Respond with JSON: {{\"category\": \"...\", \"confidence\": 0.0-1.0, "
            f"\"reasoning\": \"...\"}}"
        )
        response = await self._call_ollama(
            model=self.config.triage_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return self._parse_response(response)

    async def _run_escalation(
        self, domain: str, triage_result: dict[str, Any]
    ) -> dict[str, Any]:
        prompt = (
            f"A triage classifier marked the domain '{domain}' as "
            f"'{triage_result.get('category', 'unknown')}' with confidence "
            f"{triage_result.get('confidence', 0)}. Reasoning: "
            f"{triage_result.get('reasoning', 'N/A')}.\n\n"
            f"Perform a deeper analysis. Respond with JSON: "
            f"{{\"category\": \"...\", \"confidence\": 0.0-1.0, \"reasoning\": \"...\"}}"
        )
        response = await self._call_ollama(
            model=self.config.escalation_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return self._parse_response(response)

    async def _call_ollama(self, **kwargs) -> dict[str, Any]:
        raise NotImplementedError("Ollama client not configured")

    async def _unload_model(self, model: str):
        pass

    def _parse_response(self, response: dict[str, Any]) -> dict[str, Any]:
        content = response.get("message", {}).get("content", "{}")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"category": "unknown", "confidence": 0.0, "reasoning": content}
