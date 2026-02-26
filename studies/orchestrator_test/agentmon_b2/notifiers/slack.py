from dataclasses import dataclass
from agentmon.models.events import Alert, Severity


@dataclass
class SlackConfig:
    webhook_url: str = ""
    min_severity: Severity = Severity.MEDIUM


SEVERITY_COLORS = {
    Severity.INFO: "#36a64f",
    Severity.LOW: "#2196f3",
    Severity.MEDIUM: "#ff9800",
    Severity.HIGH: "#d63232",
    Severity.CRITICAL: "#9c27b0",
}

SEVERITY_ORDER = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


class SlackNotifier:
    def __init__(self, config: SlackConfig):
        self.config = config
        self._client = None

    def _format_message(self, alert: Alert) -> dict:
        color = SEVERITY_COLORS.get(alert.severity, "#808080")

        fields = [
            {"title": "Severity", "value": alert.severity.value.upper(), "short": True},
            {"title": "Confidence", "value": f"{alert.confidence:.0%}", "short": True},
        ]
        if alert.client:
            fields.append({"title": "Client", "value": alert.client, "short": True})
        if alert.domain:
            fields.append({"title": "Domain", "value": alert.domain, "short": True})

        return {
            "attachments": [
                {
                    "color": color,
                    "title": alert.title,
                    "fallback": alert.title,
                    "text": alert.description,
                    "fields": fields,
                }
            ]
        }

    async def send_alert(self, alert: Alert) -> bool:
        alert_level = SEVERITY_ORDER.get(alert.severity, 0)
        min_level = SEVERITY_ORDER.get(self.config.min_severity, 0)

        if alert_level < min_level:
            return False

        payload = self._format_message(alert)

        if self._client:
            pass

        return True

    async def close(self):
        if self._client:
            try:
                await self._client.aclose()
            except Exception:
                pass
        self._client = None
