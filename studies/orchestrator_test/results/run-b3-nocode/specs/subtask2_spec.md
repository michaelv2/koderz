# Subtask 2: Syslog Receiver + Parsers

Implement two files for a DNS anomaly detection system's syslog ingestion layer.

## File 1: `agentmon/collectors/syslog_receiver.py`

### SyslogMessage (dataclass)
- Fields: `timestamp` (datetime), `hostname` (str), `tag` (str), `message` (str), `facility` (int, default=0), `severity` (int, default=0)

### SyslogConfig (dataclass)
- Fields: `port` (int), `protocol` (str — "tcp" or "udp"), `bind_address` (str, default="0.0.0.0"), `allowed_ips` (list[str] or None, default=None)

### parse_syslog_message(raw: str) -> SyslogMessage | None
Parse a raw syslog string into a SyslogMessage. Must handle:

1. **RFC 3164** format: `<PRI>TIMESTAMP HOSTNAME TAG[PID]: MESSAGE`
   - Example: `<30>Feb 10 12:34:56 pihole dnsmasq[123]: query[A] example.com from 192.168.1.50`
   - Priority byte `<PRI>`: facility = PRI // 8, severity = PRI % 8
   - Tag extraction: the process name (e.g., "dnsmasq"), may include `[PID]` suffix

2. **RFC 5424** format: `<PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID SD MSG`
   - Example: `<30>1 2026-02-10T12:34:56Z pihole dnsmasq 123 - - query[A] test.com from 10.0.0.1`
   - Detect by checking if character after `>` is a digit followed by a space

3. **Fallback**: Any unrecognized format — return SyslogMessage with the raw text as `message`, empty hostname and tag

4. **Oversized messages** (>8192 chars): handle gracefully (return None or truncated result)

### SyslogReceiver
- Constructor: `__init__(self, config: SyslogConfig, handler: Callable)` — handler is an async callable that receives a SyslogMessage
- `async start()` — starts the server:
  - TCP: use `asyncio.start_server`. For each connection, read lines and parse them. Check `allowed_ips` before processing — if the client IP is not in the allowlist, close the connection without calling handler.
  - UDP: use `loop.create_datagram_endpoint` with a custom DatagramProtocol. Parse each datagram.
- `async stop()` — cleanly shuts down the server
- `is_running` property — returns True if server is active

## File 2: `agentmon/collectors/syslog_parsers.py`

### PiholeParser
- `can_parse(tag: str) -> bool` — returns True if tag is one of: "dnsmasq", "dnsmasq-dhcp", "pihole-FTL", "pihole" (case-insensitive check)
- `parse(msg: SyslogMessage) -> tuple[DNSEvent | None, ConnectionEvent | None]`:
  - Parse the message text for dnsmasq log patterns:
    - `query[TYPE] DOMAIN from CLIENT` → DNSEvent with blocked=False, query_type=TYPE
    - `gravity blocked DOMAIN from CLIENT` → DNSEvent with blocked=True
    - `gravity blocked DOMAIN is 0.0.0.0` (no client) → DNSEvent with client="__BLOCK_NOTIFICATION__", blocked=True
    - `forwarded ...` or `reply ...` → return (None, None)
  - Use msg.timestamp for the event timestamp
  - Return tuple of (DNSEvent or None, ConnectionEvent or None). ConnectionEvent is always None for dnsmasq.

### route_message(msg: SyslogMessage) -> tuple[DNSEvent | None, ConnectionEvent | None]
- Maintain a list of known parsers (at minimum PiholeParser)
- For each parser, check if `can_parse(msg.tag)` returns True; if so, delegate to that parser
- If no parser matches, return (None, None)

Import DNSEvent and ConnectionEvent from `agentmon.models.events`.
Import SyslogMessage from `agentmon.collectors.syslog_receiver`.

Write ONLY these two files. Output them as two separate fenced code blocks, each preceded by a comment with the file path.
