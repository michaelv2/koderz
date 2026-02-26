# Subtask 5: CLI + Alerting + Configuration

Implement TOML config loading, client hostname resolver, Slack notifier, and Click CLI for the `agentmon` DNS anomaly detection system.

## File Structure

Put `# path/to/file.py` as the first line in each code block. Produce these files:

- `agentmon/config.py`
- `agentmon/resolver.py`
- `agentmon/notifiers/__init__.py` (empty)
- `agentmon/notifiers/slack.py`
- `agentmon/cli.py`

## Module: `agentmon/config.py`

### `load_config(path: str) -> dict`
- If file exists: load TOML using `tomllib` (Python 3.11+ stdlib) or `tomli`
- If file does NOT exist: return sensible defaults without crashing
- Defaults should include at least: `{"database": {"path": ":memory:"}, "syslog": {"port": 1514, "protocol": "tcp"}, "analyzer": {}, "slack": {"enabled": False, "webhook_url": ""}}`
- Environment variable override: if `AGENTMON_SLACK_WEBHOOK` is set, override `config["slack"]["webhook_url"]` with that value and set `config["slack"]["enabled"] = True`
- Always ensure the returned dict has "database", "syslog", "analyzer", "slack" keys

## Module: `agentmon/resolver.py`

### `ResolverConfig` (dataclass)
- `enabled`: bool = True
- `mappings`: dict[str, str] = field(default_factory=dict) — maps IP to hostname
- `strip_suffix`: bool = False

### `ClientResolver`
- `__init__(self, config: ResolverConfig)`: stores config, initializes internal DNS cache

#### `resolve(self, ip: str) -> str`
1. If resolver is disabled (config.enabled=False): return the raw IP
2. Check explicit mappings first: if IP is in config.mappings, use that name
3. Otherwise try reverse DNS via `socket.gethostbyaddr(ip)`. If it fails, return raw IP.
4. If `config.strip_suffix` is True: take just the first label (split hostname on "." and take [0])
5. Return the resolved hostname

#### `get_cache_stats(self) -> dict`
Return dict with at least `"mappings"` key = number of entries in config.mappings.

## Module: `agentmon/notifiers/slack.py`

### `SlackConfig` (dataclass)
- `webhook_url`: str
- `min_severity`: Severity = Severity.MEDIUM (import from agentmon.models.events)

### `SlackNotifier`
- `__init__(self, config: SlackConfig)`: stores config, may create an httpx.AsyncClient as `self._client`

#### `async send_alert(self, alert: Alert) -> bool`
- Compare alert.severity against config.min_severity. Severity ordering: INFO < LOW < MEDIUM < HIGH < CRITICAL
- If alert severity is below min_severity: return False without making any HTTP request
- Otherwise: format message and POST to webhook_url. Return True on success.
- Use the severity ordering by comparing the list index of alert.severity.value vs config.min_severity.value in ["info", "low", "medium", "high", "critical"]

#### `_format_message(self, alert: Alert) -> dict`
Format Slack webhook payload. Must return dict with "attachments" key containing a list. First attachment must have:
- `"color"`: a red-ish hex color for HIGH/CRITICAL (one of: "#ff0000", "#cc0000", "#d63232", "danger")
- `"title"` or `"fallback"`: must contain the alert.title string
- Include alert details (description, client, domain, etc.) in fields

#### `async close(self)`
Clean up resources. Must not raise exceptions.

## Module: `agentmon/cli.py`

### Click CLI with these commands under a `main` group:

```
@click.group()
def main(): ...
```

Required commands (all should accept `--help`):

1. **listen** — must have `--port`, `--protocol`, `--learning`, `--llm` options
2. **stats** — show statistics
3. **alerts** — show alerts
4. **baseline** — manage baseline
5. **cleanup** — clean old data
6. **feeds** — manage threat feeds

Each command just needs to exist with the right options and print a placeholder message. The commands do not need full implementation — the tests only check that commands exist and have the right flags.
