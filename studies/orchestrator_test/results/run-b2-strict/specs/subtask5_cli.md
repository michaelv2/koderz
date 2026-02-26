# Subtask 5: CLI + Alerting + Configuration

Implement FOUR Python files. Output them as FOUR separate fenced code blocks, clearly labeled with file paths.

## File 1: `agentmon/config.py`

### Imports
```python
from __future__ import annotations
import os
from typing import Any, Dict
```

### Default config structure:
```python
_DEFAULTS = {
    "database": {"path": "/var/lib/agentmon/events.db"},
    "syslog": {"port": 514, "protocol": "tcp", "bind_address": "0.0.0.0"},
    "analyzer": {
        "entropy_threshold": 3.5,
        "learning_mode": False,
        "known_bad_patterns": ["c2-", "beacon", "malware", "rat-"],
        "allowlist": [],
        "ignore_suffixes": [".local", ".lan", ".arpa"],
    },
    "llm": {"enabled": False, "triage_model": "llama3.2:3b", "escalation_model": "llama3.3:70b"},
    "slack": {"enabled": False, "webhook_url": "", "min_severity": "medium"},
    "resolver": {"enabled": True, "strip_suffix": False, "mappings": {}},
}
```

### `_deep_merge(base: dict, override: dict) -> dict`
Recursively merge override into base. If both values are dicts, recurse. Otherwise, override wins.

### `load_config(config_path: str) -> Dict[str, Any]`
1. Start with copy of _DEFAULTS (use `import copy; copy.deepcopy(_DEFAULTS)`)
2. If config_path exists, try to load TOML:
   ```python
   try:
       import tomllib
   except ImportError:
       import tomli as tomllib
   ```
   - If file doesn't exist, just use defaults (no error)
3. Deep merge TOML values into defaults
4. Apply environment variable overrides:
   - `AGENTMON_SLACK_WEBHOOK`: If set, override `config["slack"]["webhook_url"]` AND set `config["slack"]["enabled"] = True`
   - `AGENTMON_DB_PATH`: If set, override `config["database"]["path"]`
5. Return config

IMPORTANT: If the config file doesn't exist, DO NOT raise an error. Just return defaults.

## File 2: `agentmon/resolver.py`

### Imports
```python
from __future__ import annotations
import socket
from dataclasses import dataclass, field
from typing import Dict, Optional
```

### `ResolverConfig` dataclass
Fields:
- `enabled`: bool = True
- `strip_suffix`: bool = False
- `mappings`: Dict[str, str] = field(default_factory=dict)

### `ClientResolver` class

Constructor: `__init__(self, config: ResolverConfig)`
- `self.config = config`
- `self._cache: Dict[str, str] = {}`

#### `resolve(self, ip: str) -> str`
1. If NOT enabled, return ip directly
2. Check explicit mappings first: if ip in config.mappings, use that name
3. If not in mappings, check cache
4. If not in cache, try reverse DNS: `socket.gethostbyaddr(ip)` — returns (hostname, aliases, addresses). Use hostname. If fails, use ip as fallback
5. If strip_suffix enabled, strip everything after first dot from hostname: `hostname.split(".")[0]`
6. Cache and return result

#### `get_cache_stats(self) -> Dict[str, int]`
Return: `{"mappings": len(config.mappings), "cached": len(self._cache)}`

## File 3: `agentmon/notifiers/slack.py`

### Imports
```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
from agentmon.models.events import Alert, Severity
```

### Severity color mapping:
```python
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
```

### `SlackConfig` dataclass
Fields:
- `webhook_url`: str = ""
- `min_severity`: Severity = Severity.MEDIUM
- `channel`: Optional[str] = None

### `SlackNotifier` class

Constructor: `__init__(self, config: SlackConfig)`
- `self.config = config`
- `self._client = None`  # httpx client placeholder

#### `async send_alert(self, alert: Alert) -> bool`
1. Check severity filtering: if alert severity < config min_severity, return False
   - Compare using _SEVERITY_ORDER dict
2. Format the message using `_format_message(alert)`
3. Try to send via httpx POST to webhook_url (will be mocked, so having the structure is enough)
4. Return True on success, False on failure

For the test, the key thing is: LOW severity alert with min_severity=MEDIUM should return False WITHOUT making any HTTP call.

#### `_format_message(self, alert: Alert) -> Dict[str, Any]`
Return Slack attachment format:
```python
{
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
```

#### `async close(self) -> None`
Close the httpx client if it exists. Must not raise. Simple:
```python
async def close(self) -> None:
    if self._client:
        await self._client.aclose()
        self._client = None
```

## File 4: `agentmon/cli.py`

### Imports
```python
from __future__ import annotations
import click
```

### CLI structure using Click groups:

```python
@click.group()
def main():
    """Agentmon - DNS anomaly detection system."""
    pass

@main.command()
@click.option("--port", default=514, type=int, help="Syslog port")
@click.option("--protocol", default="tcp", type=click.Choice(["tcp", "udp"]))
@click.option("--config", "config_path", default=None, help="Config file path")
@click.option("--learning/--no-learning", default=False)
@click.option("--llm/--no-llm", default=False)
@click.option("--db", default=None, help="Database path")
def listen(port, protocol, config_path, learning, llm, db):
    """Start syslog listener and detection pipeline."""
    click.echo(f"Starting listener on {protocol}://0.0.0.0:{port}")

@main.command()
@click.option("--hours", default=24, type=int)
@click.option("--db", default=None)
def stats(hours, db):
    """Show client query statistics."""
    click.echo(f"Stats for last {hours} hours")

@main.command()
@click.option("--severity", default="info")
@click.option("--limit", default=50, type=int)
@click.option("--db", default=None)
def alerts(severity, limit, db):
    """Show unacknowledged alerts."""
    click.echo(f"Alerts (min severity: {severity})")

@main.command()
@click.option("--enable/--disable", default=None)
@click.option("--db", default=None)
def baseline(enable, db):
    """Manage baseline learning mode."""
    click.echo("Baseline management")

@main.command()
@click.option("--dns-days", default=30, type=int)
@click.option("--alerts-days", default=30, type=int)
@click.option("--db", default=None)
def cleanup(dns_days, alerts_days, db):
    """Clean up old data."""
    click.echo(f"Cleaning up data older than {dns_days}/{alerts_days} days")

@main.command()
@click.option("--update/--no-update", default=False)
def feeds(update):
    """Manage threat intelligence feeds."""
    click.echo("Threat feed management")
```

The CLI commands just need to exist with the right options and help text for the tests. The tests only check `--help` output and command existence.
