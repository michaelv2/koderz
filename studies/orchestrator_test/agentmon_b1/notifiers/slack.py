from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
from agentmon.models.events import Alert, Severity

_SEVERITY_COLORS = {
    Severity.INFO: "#2196f3",
    Severity.LOW: "#4caf50",
    Severity.MEDIUM: "#ff9800",
    Severity.HIGH: "#d63232",
    Severity.CRITICAL: "#9c27b0",
}

_SEVERITY_ORDER = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


@dataclass
class SlackConfig:
    webhook_url: str = ""
    min_severity: Severity = Severity.MEDIUM
    channel: Optional[str] = None


class SlackNotifier:
    def __init__(self, config: SlackConfig):
        self.config = config
        self._client = None

    async def send_alert(self, alert: Alert) -> bool:
        if _SEVERITY_ORDER.get(alert.severity, 0) < _SEVERITY_ORDER.get(self.config.min_severity, 0):
            return False

        payload = self._format_message(alert)

        try:
            import httpx
            if self._client is None:
                self._client = httpx.AsyncClient()
            response = await self._client.post(self.config.webhook_url, json=payload)
            response.raise_for_status()
            return True
        except Exception:
            return False

    def _format_message(self, alert: Alert) -> Dict[str, Any]:
        return {
            "attachments": [
                {
                    "color": _SEVERITY_COLORS.get(alert.severity, "#808080"),
                    "title": alert.title,
                    "fallback": alert.title,
                    "text": alert.description,
                    "fields": [
                        {"title": "Severity", "value": alert.severity.value, "short": True},
                        {"title": "Client", "value": alert.client or "unknown", "short": True},
                        {"title": "Domain", "value": alert.domain or "unknown", "short": True},
                        {"title": "Analyzer", "value": alert.analyzer or "unknown", "short": True},
                        {"title": "Confidence", "value": f"{alert.confidence:.0%}", "short": True},
                    ],
                }
            ]
        }

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
