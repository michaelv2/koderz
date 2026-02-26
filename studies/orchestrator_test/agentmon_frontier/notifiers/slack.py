from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from agentmon.models.events import Alert, Severity

_SEVERITY_ORDER = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}

_SEVERITY_COLORS = {
    Severity.INFO: "#2196f3",
    Severity.LOW: "#4caf50",
    Severity.MEDIUM: "#ff9800",
    Severity.HIGH: "#d63232",
    Severity.CRITICAL: "#9c27b0",
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

    def _format_message(self, alert: Alert) -> dict[str, Any]:
        color = _SEVERITY_COLORS.get(alert.severity, "#808080")
        fields = []
        if alert.client:
            fields.append({"title": "Client", "value": alert.client, "short": True})
        if alert.domain:
            fields.append({"title": "Domain", "value": alert.domain, "short": True})
        if alert.analyzer:
            fields.append({"title": "Analyzer", "value": alert.analyzer, "short": True})
        fields.append(
            {"title": "Confidence", "value": f"{alert.confidence:.0%}", "short": True}
        )

        attachment = {
            "color": color,
            "title": alert.title,
            "fallback": alert.title,
            "text": alert.description,
            "fields": fields,
            "ts": int(alert.timestamp.timestamp()),
        }

        payload: dict[str, Any] = {"attachments": [attachment]}
        if self.config.channel:
            payload["channel"] = self.config.channel
        return payload

    async def send_alert(self, alert: Alert) -> bool:
        min_level = _SEVERITY_ORDER.get(self.config.min_severity, 0)
        alert_level = _SEVERITY_ORDER.get(alert.severity, 0)
        if alert_level < min_level:
            return False

        payload = self._format_message(alert)

        try:
            import httpx

            if self._client is None:
                self._client = httpx.AsyncClient()
            resp = await self._client.post(self.config.webhook_url, json=payload)
            return resp.status_code == 200
        except Exception:
            return False

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None
