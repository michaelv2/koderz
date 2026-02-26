# Fix: Syslog parser should use current time as event timestamp

In `agentmon/collectors/syslog_receiver.py`, the `parse_syslog_message` function parses the timestamp from the syslog line (e.g. "Feb 10 12:00:00"). RFC 3164 timestamps don't include a year, so these timestamps can end up in the past. This breaks downstream time-window checks.

## Required Change

In `parse_syslog_message`, always set `timestamp=datetime.now(timezone.utc)` on the returned SyslogMessage, regardless of what timestamp appears in the raw syslog line. The receive time (now) is more reliable than the parsed syslog timestamp for real-time processing.

This is a one-line change: wherever the SyslogMessage is created with a parsed timestamp, replace it with `datetime.now(timezone.utc)`.

Rewrite the full file. Put `# agentmon/collectors/syslog_receiver.py` as the first line in the code block.
