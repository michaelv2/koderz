# agentmon/config.py
import os
try:
    import tomllib
except ImportError:
    import tomli as tomllib


def load_config(path: str) -> dict:
    """Load TOML config file. If file doesn't exist, return defaults.

    Apply environment variable overrides:
    - AGENTMON_SLACK_WEBHOOK -> config["slack"]["webhook_url"] AND set config["slack"]["enabled"] = True

    Default config structure:
    {
        "database": {"path": "/var/lib/agentmon/events.db"},
        "syslog": {"port": 514, "protocol": "tcp"},
        "analyzer": {"entropy_threshold": 3.5, "learning_mode": True, "known_bad_patterns": []},
        "slack": {"enabled": False, "webhook_url": ""},
        "llm": {"triage_model": "llama3.2:3b", "escalation_model": "llama3.3:70b"},
    }
    """
    defaults = {
        "database": {"path": "/var/lib/agentmon/events.db"},
        "syslog": {"port": 514, "protocol": "tcp"},
        "analyzer": {"entropy_threshold": 3.5, "learning_mode": True, "known_bad_patterns": []},
        "slack": {"enabled": False, "webhook_url": ""},
        "llm": {"triage_model": "llama3.2:3b", "escalation_model": "llama3.3:70b"},
    }

    try:
        with open(path, "rb") as f:
            config = tomllib.load(f)
    except (FileNotFoundError, OSError):
        config = {}

    # Merge: file config overrides defaults
    for section, values in defaults.items():
        if section not in config:
            config[section] = dict(values)
        else:
            for key, default_val in values.items():
                if key not in config[section]:
                    config[section][key] = default_val

    # Environment variable overrides
    slack_webhook = os.environ.get("AGENTMON_SLACK_WEBHOOK")
    if slack_webhook:
        config.setdefault("slack", {})
        config["slack"]["webhook_url"] = slack_webhook
        config["slack"]["enabled"] = True

    return config


# agentmon/resolver.py
import socket
from dataclasses import dataclass, field


@dataclass
class ResolverConfig:
    enabled: bool = True
    mappings: dict = field(default_factory=dict)  # {ip: hostname}
    strip_suffix: bool = False


class ClientResolver:
    def __init__(self, config: ResolverConfig):
        self.config = config
        self._cache = {}

    def resolve(self, ip: str) -> str:
        """Resolve IP to hostname.

        Priority:
        1. If disabled, return raw IP
        2. Check explicit mappings
        3. Try reverse DNS (catch exceptions, return IP on failure)
        4. Apply strip_suffix if configured (keep only first label)
        5. Cache result
        """
        if not self.config.enabled:
            return ip

        if ip in self._cache:
            return self._cache[ip]

        # Check explicit mappings
        if ip in self.config.mappings:
            hostname = self.config.mappings[ip]
            if self.config.strip_suffix and "." in hostname:
                hostname = hostname.split(".")[0]
            self._cache[ip] = hostname
            return hostname

        # Try reverse DNS
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            if self.config.strip_suffix and "." in hostname:
                hostname = hostname.split(".")[0]
            self._cache[ip] = hostname
            return hostname
        except (socket.herror, socket.gaierror, OSError):
            self._cache[ip] = ip
            return ip

    def get_cache_stats(self) -> dict:
        """Return stats about mappings and cache."""
        return {
            "mappings": len(self.config.mappings),
            "cached": len(self._cache),
        }


# agentmon/notifiers/slack.py
from dataclasses import dataclass
from agentmon.models.events import Alert, Severity


@dataclass
class SlackConfig:
    webhook_url: str = ""
    min_severity: Severity = Severity.MEDIUM


SEVERITY_COLORS = {
    Severity.INFO: "#36a64f",     # green
    Severity.LOW: "#2196f3",      # blue
    Severity.MEDIUM: "#ff9800",   # orange
    Severity.HIGH: "#d63232",     # red
    Severity.CRITICAL: "#9c27b0", # purple
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
        """Format alert as Slack message with attachments.

        Returns dict with "attachments" key containing list with one attachment.
        The attachment has:
        - "color": severity-based color (red-ish for HIGH)
        - "title" or "fallback": contains the alert title
        - "fields": list of field dicts
        """
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
        """Send alert to Slack. Returns False if below min_severity.

        Compare severity levels: if alert severity < min_severity, skip.
        """
        alert_level = SEVERITY_ORDER.get(alert.severity, 0)
        min_level = SEVERITY_ORDER.get(self.config.min_severity, 0)

        if alert_level < min_level:
            return False

        payload = self._format_message(alert)

        # In real implementation, would POST to webhook_url
        if self._client:
            # Would use httpx to send
            pass

        return True

    async def close(self):
        """Close any open connections. Must not raise."""
        if self._client:
            try:
                await self._client.aclose()
            except Exception:
                pass
        self._client = None


# agentmon/cli.py
import click


@click.group()
def main():
    """agentmon — DNS anomaly detection system."""
    pass


@main.command()
@click.option("--port", type=int, default=514, help="Syslog listen port")
@click.option("--protocol", type=click.Choice(["tcp", "udp"]), default="tcp", help="Syslog protocol")
@click.option("--config", "config_path", type=click.Path(), default=None, help="Config file path")
@click.option("--learning", is_flag=True, default=False, help="Enable learning mode")
@click.option("--llm", is_flag=True, default=False, help="Enable LLM classification")
def listen(port, protocol, config_path, learning, llm):
    """Listen for syslog messages and analyze DNS traffic."""
    click.echo(f"Listening on {protocol}:{port}")


@main.command()
@click.option("--hours", type=int, default=24, help="Time window in hours")
@click.option("--db", "db_path", type=click.Path(), default=None, help="Database path")
def stats(hours, db_path):
    """Show client query statistics."""
    click.echo("Stats")


@main.command()
@click.option("--severity", type=click.Choice(["info", "low", "medium", "high", "critical"]), default="info")
@click.option("--limit", type=int, default=50, help="Max alerts to show")
@click.option("--db", "db_path", type=click.Path(), default=None, help="Database path")
def alerts(severity, limit, db_path):
    """Show recent alerts."""
    click.echo("Alerts")


@main.command()
@click.option("--mode", type=click.Choice(["start", "stop", "status"]), default="status")
@click.option("--db", "db_path", type=click.Path(), default=None, help="Database path")
def baseline(mode, db_path):
    """Manage baseline learning."""
    click.echo(f"Baseline {mode}")


@main.command()
@click.option("--dns-days", type=int, default=30, help="DNS retention days")
@click.option("--alerts-days", type=int, default=30, help="Alerts retention days")
@click.option("--db", "db_path", type=click.Path(), default=None, help="Database path")
def cleanup(dns_days, alerts_days, db_path):
    """Clean up old data."""
    click.echo("Cleanup")


@main.command()
@click.option("--update", is_flag=True, help="Download latest feeds")
@click.option("--cache-dir", type=click.Path(), default=None, help="Feed cache directory")
def feeds(update, cache_dir):
    """Manage threat feeds."""
    click.echo("Feeds")
