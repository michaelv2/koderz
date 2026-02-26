# Fix: Syslog parser timestamp

Fix `agentmon/collectors/syslog_receiver.py` — the `parse_syslog_message` function.

Put `# agentmon/collectors/syslog_receiver.py` as the first line in the code block. Rewrite the full file.

## The Bug

When parsing syslog messages, the parsed timestamp (e.g. "Feb 10 12:00:00") is used as-is. This causes problems in integration tests where events from old timestamps are not found by time-window queries.

## The Fix

In `parse_syslog_message`, always use `datetime.now(timezone.utc)` as the timestamp for the SyslogMessage. The syslog timestamp from the raw message is unreliable (may be from a different timezone, may have no year, etc.). Using current receive-time is standard practice.

Everything else in the file stays the same:
- SyslogMessage dataclass (timestamp, hostname, tag, message, facility=0, severity=0)
- SyslogConfig dataclass (port, protocol, bind_address="0.0.0.0", allowed_ips=None)
- parse_syslog_message: RFC 3164 parsing, RFC 5424 parsing, fallback — all keep working but use `datetime.now(timezone.utc)` for the timestamp
- SyslogReceiver class with start(), stop(), is_running, TCP/UDP support, IP allowlist, async handler awaiting
