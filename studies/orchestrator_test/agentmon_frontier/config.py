from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]


_DEFAULTS: dict[str, Any] = {
    "database": {
        "path": "/var/lib/agentmon/events.db",
    },
    "syslog": {
        "port": 514,
        "protocol": "tcp",
        "bind_address": "0.0.0.0",
    },
    "analyzer": {
        "entropy_threshold": 3.5,
        "learning_mode": False,
        "known_bad_patterns": ["c2-", "beacon", "malware", "rat-"],
        "allowlist": [],
        "ignore_suffixes": [".local", ".lan", ".arpa"],
    },
    "llm": {
        "enabled": False,
        "triage_model": "llama3.2:3b",
        "escalation_model": "llama3.3:70b",
    },
    "slack": {
        "enabled": False,
        "webhook_url": "",
        "min_severity": "medium",
    },
    "resolver": {
        "enabled": True,
        "strip_suffix": False,
        "mappings": {},
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_config(config_path: str) -> dict[str, Any]:
    config = dict(_DEFAULTS)

    # Deep-copy defaults
    config = {k: (dict(v) if isinstance(v, dict) else v) for k, v in _DEFAULTS.items()}

    path = Path(config_path)
    if path.exists():
        with open(path, "rb") as f:
            file_config = tomllib.load(f)
        config = _deep_merge(config, file_config)

    # Environment variable overrides
    slack_webhook = os.environ.get("AGENTMON_SLACK_WEBHOOK")
    if slack_webhook:
        if "slack" not in config:
            config["slack"] = {}
        config["slack"]["webhook_url"] = slack_webhook
        config["slack"]["enabled"] = True

    db_path = os.environ.get("AGENTMON_DB_PATH")
    if db_path:
        if "database" not in config:
            config["database"] = {}
        config["database"]["path"] = db_path

    return config
