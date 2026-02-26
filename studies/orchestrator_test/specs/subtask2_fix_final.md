# Fix: PiholeParser query_type case + SyslogReceiver IP allowlist

Two bugs remain in subtask 2:

## Bug 1: query_type is lowercased

In `syslog_parsers.py`, the PiholeParser `parse` method is returning the query_type in lowercase (e.g. "a" instead of "A"). The regex extracts the query type from `query[A]` but it is being lowercased somewhere. The query_type field must preserve the original case from the log message. If the regex is using `re.IGNORECASE`, it still extracts the original text — just don't call `.lower()` on the query type.

## Bug 2: IP allowlist not working

In `syslog_receiver.py`, the SyslogReceiver's TCP handler is not checking `allowed_ips` correctly. When a TCP client connects, the handler must:
1. Get the client IP from `writer.get_extra_info('peername')[0]`
2. If `config.allowed_ips` is not None and the client IP is NOT in `config.allowed_ips`, close the connection immediately without calling the handler
3. Only process messages if the IP is allowed

Rewrite both files completely. Put `# agentmon/collectors/syslog_parsers.py` and `# agentmon/collectors/syslog_receiver.py` as the first line in each code block.
