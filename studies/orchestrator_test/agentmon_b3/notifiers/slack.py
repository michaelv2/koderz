from dataclasses import dataclass
from typing import Any, Dict, Optional

from agentmon.models.events import Alert, Severity

SEVERITY_ORDER = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}

COLOR_MAP = {
    Severity.INFO: "#36a64f",
    Severity.LOW: "#36a64f",
    Severity.MEDIUM: "#ffae42",
    Severity.HIGH: "#ff0000",
    Severity.CRITICAL: "#cc0000",
}


@dataclass
class SlackConfig:
    webhook_url: str
    min_severity: Severity = Severity.MEDIUM


class SlackNotifier:
    def __init__(self, config: SlackConfig):
        self.config = config
        self._client: Optional[Any] = None

    async def send_alert(self, alert: Alert) -> bool:
        if SEVERITY_ORDER.get(alert.severity, 0) < SEVERITY_ORDER.get(self.config.min_severity, 0):
            return False
        if not self.config.webhook_url:
            return False
        # In production, would POST to webhook_url
        return True

    def _format_message(self, alert: Alert) -> Dict[str, Any]:
        color = COLOR_MAP.get(alert.severity, "#ff0000")
        attachment = {
            "fallback": alert.title,
            "color": color,
            "title": alert.title,
            "fields": [
                {"title": "Severity", "value": alert.severity.value, "short": True},
                {"title": "Domain", "value": getattr(alert, "domain", ""), "short": True},
                {"title": "Client", "value": getattr(alert, "client", ""), "short": True},
                {"title": "Confidence", "value": f"{getattr(alert, 'confidence', 0.0):.2%}", "short": True},
            ],
        }
        return {"attachments": [attachment]}

    async def close(self) -> None:
        pass
