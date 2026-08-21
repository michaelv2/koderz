import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


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
    domain = re.sub(r"[\x00-\x1f\x7f]", "", domain)
    domain = re.sub(r"[^A-Za-z0-9._-]", "", domain)
    return domain[:253]


class DomainClassifier:
    def __init__(self, config: LLMConfig):
        self.config = config
        self._cache: Dict[str, ClassificationResult] = {}

    async def _call_ollama(self, **kwargs) -> dict:
        raise NotImplementedError("Should be mocked in tests")

    async def _unload_model(self, model: str) -> None:
        raise NotImplementedError("Should be mocked in tests")

    def _parse_response(self, response: dict) -> dict:
        content = response.get("message", {}).get("content", "")
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return {"category": "unknown", "confidence": 0.0, "reasoning": content}

    def _to_category(self, category_str: str) -> DomainCategory:
        category_str = category_str.lower()
        try:
            return DomainCategory(category_str)
        except ValueError:
            return DomainCategory.UNKNOWN

    async def classify(self, domain: str) -> ClassificationResult:
        cached = self._cache.get(domain)
        if cached is not None:
            return cached

        sanitized = sanitize_domain_for_prompt(domain)

        # Triage call
        triage_resp = await self._call_ollama(
            model=self.config.triage_model,
            prompt=f"Classify the domain '{sanitized}'.",
        )
        triage_data = self._parse_response(triage_resp)
        triage_category_str = triage_data.get("category", "unknown").lower()
        triage_category = self._to_category(triage_category_str)
        triage_confidence = float(triage_data.get("confidence", 0.0))
        triage_reasoning = triage_data.get("reasoning", "")

        result = ClassificationResult(
            domain=domain,
            category=triage_category,
            confidence=triage_confidence,
            reasoning=triage_reasoning,
        )

        # Escalation check
        needs_escalation = (
            triage_category_str == "suspicious"
            or triage_confidence < self.config.escalation_threshold
        )

        if needs_escalation:
            esc_resp = await self._call_ollama(
                model=self.config.escalation_model,
                prompt=f"Escalate classification for domain '{sanitized}'.",
            )
            esc_data = self._parse_response(esc_resp)
            esc_category_str = esc_data.get("category", "unknown").lower()
            result.category = self._to_category(esc_category_str)
            result.confidence = float(esc_data.get("confidence", 0.0))
            result.reasoning = esc_data.get("reasoning", "")
            result.escalated = True
            result.triage_category = triage_category_str

        self._cache[domain] = result
        return result
