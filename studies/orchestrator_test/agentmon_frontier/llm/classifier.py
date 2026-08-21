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
    escalation_model: str = "llama3.3:70b"
    ollama_host: str = "http://localhost:11434"
    escalation_threshold: float = 0.7
    cache_ttl: int = 86400  # 24 hours


_UNSAFE_CHARS = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_MAX_DOMAIN_LENGTH = 253


def sanitize_domain_for_prompt(domain: str) -> str:
    clean = _UNSAFE_CHARS.sub("", domain)
    if len(clean) > _MAX_DOMAIN_LENGTH:
        clean = clean[:_MAX_DOMAIN_LENGTH]
    return clean


def _parse_category(raw: str) -> DomainCategory:
    mapping = {v.value: v for v in DomainCategory}
    normalized = raw.strip().lower().replace(" ", "_")
    return mapping.get(normalized, DomainCategory.UNKNOWN)


class DomainClassifier:
    def __init__(self, config: LLMConfig):
        self.config = config
        self._cache: dict[str, tuple[ClassificationResult, float]] = {}

    async def _call_ollama(self, **kwargs) -> dict[str, Any]:
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.config.ollama_host}/api/chat",
                json=kwargs,
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()

    async def _unload_model(self, model: str):
        pass

    async def classify(self, domain: str) -> ClassificationResult:
        # Check cache
        now = time.time()
        if domain in self._cache:
            result, expiry = self._cache[domain]
            if expiry > now:
                return result

        clean_domain = sanitize_domain_for_prompt(domain)

        # Tier 1: Triage
        triage_resp = await self._call_ollama(
            model=self.config.triage_model,
            messages=[{
                "role": "user",
                "content": (
                    f"Classify this domain as one of: benign, suspicious, likely_malicious, "
                    f"dga, advertising, tracking, cdn, cloud_provider, api_service.\n"
                    f"Domain: {clean_domain}\n"
                    f"Respond with JSON: {{\"category\": \"...\", \"confidence\": 0.0-1.0, \"reasoning\": \"...\"}}"
                ),
            }],
        )

        triage_data = json.loads(triage_resp["message"]["content"])
        triage_category = triage_data.get("category", "unknown")
        triage_confidence = float(triage_data.get("confidence", 0.5))

        category = _parse_category(triage_category)

        # If suspicious or low confidence, escalate
        needs_escalation = (
            category == DomainCategory.SUSPICIOUS
            or (category not in (DomainCategory.BENIGN, DomainCategory.CDN,
                                 DomainCategory.CLOUD_PROVIDER, DomainCategory.API_SERVICE)
                and triage_confidence < self.config.escalation_threshold)
        )

        if needs_escalation:
            escalation_resp = await self._call_ollama(
                model=self.config.escalation_model,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Perform a deep analysis of this domain.\n"
                        f"Initial triage classified it as '{triage_category}' with confidence {triage_confidence}.\n"
                        f"Domain: {clean_domain}\n"
                        f"Respond with JSON: {{\"category\": \"...\", \"confidence\": 0.0-1.0, \"reasoning\": \"...\"}}"
                    ),
                }],
            )

            esc_data = json.loads(escalation_resp["message"]["content"])
            category = _parse_category(esc_data.get("category", "unknown"))
            confidence = float(esc_data.get("confidence", 0.5))
            reasoning = esc_data.get("reasoning", "")

            result = ClassificationResult(
                domain=domain,
                category=category,
                confidence=confidence,
                reasoning=reasoning,
                escalated=True,
                triage_category=triage_category,
            )
        else:
            result = ClassificationResult(
                domain=domain,
                category=category,
                confidence=triage_confidence,
                reasoning=triage_data.get("reasoning", ""),
                escalated=False,
                triage_category=triage_category,
            )

        await self._unload_model(self.config.triage_model)

        # Cache result
        self._cache[domain] = (result, now + self.config.cache_ttl)
        return result
