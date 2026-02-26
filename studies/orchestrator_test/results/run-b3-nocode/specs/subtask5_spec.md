# Subtask 5: CLI + Alerting + Configuration

Implement four files for a DNS anomaly detection system.

## File 1: `agentmon/config.py`

### load_config(path: str) -> dict
- If the file exists, load it as TOML (use tomllib for Python 3.11+, or tomli as fallback)
- If the file does not exist, return a dict with sensible defaults:
  ```
  {"database": {"path": "agentmon.db"}, "syslog": {"port": 514, "protocol": "udp"}, "analyzer": {}, "slack": {"enabled": False, "webhook_url": ""}}
  ```
- After loading, apply environment variable overrides:
  - If env var `AGENTMON_SLACK_WEBHOOK` is set and non-empty: set config["slack"]["webhook_url"] to its value AND set config["slack"]["enabled"] to True
- Return the config dict. Always ensure "slack" key exists.

## File 2: `agentmon/resolver.py`

### ResolverConfig (dataclass)
- Fields: `enabled` (bool, default=True), `mappings` (dict[str, str], default_factory=dict), `strip_suffix` (bool, default=False), `suffix_to_strip` (str, default="")

### ClientResolver
- Constructor: `__init__(self, config: ResolverConfig)` — stores config, initializes a cache dict
- `resolve(ip: str) -> str`:
  1. If not enabled, return the raw IP
  2. Check explicit mappings first: if ip is in config.mappings, use that hostname
  3. If strip_suffix is True: strip everything after the first "." in the hostname (e.g., "myhost.home.lan" → "myhost")
  4. If no mapping found, try reverse DNS lookup (socket.gethostbyaddr). If that fails, return the raw IP.
  5. Cache the result
- `get_cache_stats() -> dict` — return {"mappings": len(config.mappings), "cache_size": len(cache)}

## File 3: `agentmon/notifiers/slack.py`

### SlackConfig (dataclass)
- Fields: `webhook_url` (str), `min_severity` (Severity, default=Severity.MEDIUM) where Severity is from agentmon.models.events

### SlackNotifier
- Constructor: `__init__(self, config: SlackConfig)` — stores config, creates an internal _client attribute (can be None or a mock-friendly object)
- `async send_alert(alert: Alert) -> bool`:
  - Compare alert.severity against config.min_severity. Severity ordering: INFO < LOW < MEDIUM < HIGH < CRITICAL.
  - If alert severity is below min_severity, return False without sending
  - Otherwise, format the message and send via webhook. Return True on success.
- `_format_message(alert: Alert) -> dict`:
  - Return a Slack-compatible payload dict with "attachments" key
  - Each attachment has: "color" (red-ish for HIGH/CRITICAL — use "#ff0000", "#cc0000", "#d63232", or "danger"), "title" or "fallback" containing the alert.title
  - Include relevant fields (severity, domain, client, confidence, etc.)
- `async close()` — cleanup, must not raise

Import Severity and Alert from agentmon.models.events.

## File 4: `agentmon/cli.py`

### main — Click group with the following subcommands:
- `listen` — accepts flags: `--port` (int), `--protocol` (str), `--config` (path), `--learning` (flag), `--llm` (flag)
- `stats` — show statistics
- `alerts` — show alerts
- `baseline` — baseline management
- `cleanup` — data cleanup
- `feeds` — threat feed management

Each command just needs to be declared with the right Click decorators and help text. The commands can have minimal implementations (e.g., click.echo("Not implemented")) — the tests only check that the commands exist and accept the right arguments.

Use `@click.group()` for `main` and `@main.command()` for each subcommand.

Write ONLY these four files. Output them as four separate fenced code blocks, each preceded by a comment with the file path.
