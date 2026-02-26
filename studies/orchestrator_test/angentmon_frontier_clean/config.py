from __future__ import annotations

import os
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def _default_config() -> dict[str, Any]:
    return {
        "database": {"path": "/var/lib/agentmon/events.db"},
        "syslog": {
            "port": 514,
            "protocol": "udp",
            "bind_address": "0.0.0.0",
        },
        "analyzer": {
            "entropy_threshold": 3.5,
            "learning_mode": False,
            "known_bad_patterns": ["c2-", "beacon", "malware", "rat-"],
            "allowlist": [],
            "ignore_suffixes": [".local", ".lan", ".arpa"],
        },
        "slack": {
            "enabled": False,
            "webhook_url": "",
            "min_severity": "medium",
        },
        "llm": {
            "enabled": False,
            "triage_model": "llama3.2:3b",
            "escalation_model": "llama3.1:8b",
            "ollama_host": "http://localhost:11434",
        },
        "resolver": {
            "enabled": True,
            "strip_suffix": False,
            "mappings": {},
        },
        "retention": {
            "dns_days": 30,
            "alerts_days": 90,
        },
    }


def load_config(path: str) -> dict[str, Any]:
    config = _default_config()

    try:
        with open(path, "rb") as f:
            file_config = tomllib.load(f)
        _deep_merge(config, file_config)
    except (FileNotFoundError, OSError):
        pass

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


def _deep_merge(base: dict, override: dict):
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
