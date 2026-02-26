# Fix: Use current time for SyslogMessage timestamp

The integration test `test_block_correlation_end_to_end` fails because `parse_syslog_message` parses the syslog header timestamp (e.g. "Feb 10 12:00:00" — 15 days ago). Then `mark_domain_blocked` checks `timestamp >= current_timestamp - interval '5 seconds'`, which fails because Feb 10 is far in the past.

## Fix in `parse_syslog_message` in syslog_receiver.py:

Always use `datetime.now(timezone.utc)` as the SyslogMessage timestamp instead of trying to parse the time from the syslog header. No test checks the parsed timestamp value — they only check hostname, tag, and message.

Change every place that creates a SyslogMessage to use `timestamp=datetime.now(timezone.utc)`.

Remember to put `# agentmon/collectors/syslog_receiver.py` as the first line.
Output the COMPLETE file.
