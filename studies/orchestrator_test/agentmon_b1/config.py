from __future__ import annotations
import os
import copy
from typing import Any, Dict

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


def _deep_merge(base: dict, override: dict) -> dict:
    for key, val in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(val, dict):
            base[key] = _deep_merge(base[key], val)
        else:
            base[key] = val
    return base


def load_config(config_path: str) -> Dict[str, Any]:
    config = copy.deepcopy(_DEFAULTS)

    if os.path.exists(config_path):
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        try:
            with open(config_path, "rb") as f:
                toml_data = tomllib.load(f)
            _deep_merge(config, toml_data)
        except Exception:
            pass

    slack_webhook = os.getenv("AGENTMON_SLACK_WEBHOOK")
    if slack_webhook:
        config["slack"]["webhook_url"] = slack_webhook
        config["slack"]["enabled"] = True

    db_path = os.getenv("AGENTMON_DB_PATH")
    if db_path:
        config["database"]["path"] = db_path

    return config
