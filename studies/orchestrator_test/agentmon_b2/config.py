import os
try:
    import tomllib
except ImportError:
    import tomli as tomllib


def load_config(path: str) -> dict:
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

    for section, values in defaults.items():
        if section not in config:
            config[section] = dict(values)
        else:
            for key, default_val in values.items():
                if key not in config[section]:
                    config[section][key] = default_val

    slack_webhook = os.environ.get("AGENTMON_SLACK_WEBHOOK")
    if slack_webhook:
        config.setdefault("slack", {})
        config["slack"]["webhook_url"] = slack_webhook
        config["slack"]["enabled"] = True

    return config
