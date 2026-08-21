from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx

from agentmon.models.events import Alert, Severity

_SEVERITY_ORDER = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}

_SEVERITY_COLORS = {
    Severity.INFO: "#36a64f",
    Severity.LOW: "#2196f3",
    Severity.MEDIUM: "#ff9800",
    Severity.HIGH: "#d63232",
    Severity.CRITICAL: "#9c27b0",
}


@dataclass
class SlackConfig:
    webhook_url: str
    min_severity: Severity = Severity.MEDIUM
    channel: Optional[str] = None


class SlackNotifier:
    def __init__(self, config: SlackConfig):
        self.config = config
        self._client = httpx.AsyncClient()

    async def send_alert(self, alert: Alert) -> bool:
        alert_order = _SEVERITY_ORDER.get(alert.severity, 0)
        min_order = _SEVERITY_ORDER.get(self.config.min_severity, 0)
        if alert_order < min_order:
            return False

        payload = self._format_message(alert)
        try:
            response = await self._client.post(
                self.config.webhook_url, json=payload
            )
            return response.status_code == 200
        except Exception:
            return False

    def _format_message(self, alert: Alert) -> dict[str, Any]:
        color = _SEVERITY_COLORS.get(alert.severity, "#808080")
        fields = [
            {"title": "Severity", "value": alert.severity.value, "short": True},
        ]
        if alert.client:
            fields.append(
                {"title": "Client", "value": alert.client, "short": True}
            )
        if alert.domain:
            fields.append(
                {"title": "Domain", "value": alert.domain, "short": True}
            )
        if alert.confidence is not None:
            fields.append(
                {
                    "title": "Confidence",
                    "value": f"{alert.confidence:.0%}",
                    "short": True,
                }
            )

        return {
            "attachments": [
                {
                    "color": color,
                    "title": alert.title,
                    "text": alert.description,
                    "fallback": alert.title,
                    "fields": fields,
                    "ts": int(alert.timestamp.timestamp()),
                }
            ]
        }

    async def close(self):
        try:
            await self._client.aclose()
        except Exception:
            pass
