import copy
import os
import sys
from pathlib import Path
from typing import Any, Dict

try:
    import tomllib
except ImportError:
    import tomli as tomllib


DEFAULT_CONFIG: Dict[str, Any] = {
    "database": {"path": "agentmon.db"},
    "syslog": {"port": 514, "protocol": "udp"},
    "analyzer": {},
    "slack": {"enabled": False, "webhook_url": ""},
}


def load_config(path: str) -> Dict[str, Any]:
    config = copy.deepcopy(DEFAULT_CONFIG)

    file_path = Path(path)
    if file_path.is_file():
        try:
            with file_path.open("rb") as f:
                file_config = tomllib.load(f)
            for key, value in file_config.items():
                if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                    config[key].update(value)
                else:
                    config[key] = value
        except Exception:
            pass

    config.setdefault("slack", {"enabled": False, "webhook_url": ""})

    webhook = os.getenv("AGENTMON_SLACK_WEBHOOK", "").strip()
    if webhook:
        config["slack"]["webhook_url"] = webhook
        config["slack"]["enabled"] = True

    return config
