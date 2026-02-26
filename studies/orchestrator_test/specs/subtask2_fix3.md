# Fix: Syslog Receiver + Parsers

Fix the following issues in the agentmon syslog collector files. Rewrite BOTH files completely.

Put `# path/to/file.py` as the first line in each code block.

## File 1: `agentmon/collectors/syslog_parsers.py`

The PiholeParser.parse() method creates DNSEvent with WRONG field names. DNSEvent is a frozen dataclass with these exact fields:
- `timestamp` (datetime)
- `client` (str) — the client IP address
- `domain` (str)
- `query_type` (str)
- `blocked` (bool)

It does NOT have: `hostname`, `tag`, `client_ip`, `message`, or `details`.

Fix parse() to construct DNSEvent correctly:
- For query pattern `query[TYPE] DOMAIN from CLIENT`: `DNSEvent(timestamp=msg.timestamp, client=CLIENT, domain=DOMAIN, query_type=TYPE, blocked=False)`
- For blocked with client `gravity blocked DOMAIN from CLIENT`: `DNSEvent(timestamp=msg.timestamp, client=CLIENT, domain=DOMAIN, query_type="A", blocked=True)`
- For blocked without client `gravity blocked DOMAIN is 0.0.0.0`: `DNSEvent(timestamp=msg.timestamp, client="__BLOCK_NOTIFICATION__", domain=DOMAIN, query_type="A", blocked=True)`
- Forward/reply lines: return (None, None)

Also include the `can_parse` method checking tags case-insensitively for: dnsmasq, dnsmasq-dhcp, pihole-FTL, pihole.

Include `route_message(msg)` free function that creates PiholeParser, checks can_parse, calls parse.

## File 2: `agentmon/collectors/syslog_receiver.py`

Three issues to fix:

1. **RFC 5424 parsing broken**: The format is `<PRI>1 YYYY-MM-DDTHH:MM:SSZ hostname app_name procid msgid sd message`. Use regex like `^<(\d+)>1\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S*)\s*(.*)$` to parse version-1 format.

2. **Handler must be awaited**: The handler is an async callable. When calling handler in TCP and UDP code paths, use `await self.handler(msg)` not just `self.handler(msg)`.

3. **TCP reading**: Use `readline()` in a loop and handle client disconnects. Each line is one syslog message.

Keep SyslogMessage dataclass (timestamp, hostname, tag, message, facility=0, severity=0).
Keep SyslogConfig dataclass (port, protocol, bind_address="0.0.0.0", allowed_ips=None).
Keep parse_syslog_message function handling RFC 3164, RFC 5424, and fallback.
Keep SyslogReceiver with start(), stop(), is_running property.
Keep IP allowlist check for TCP connections.
