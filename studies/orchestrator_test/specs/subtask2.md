# Subtask 2: Syslog Receiver + Parsers

Implement async TCP/UDP syslog receiver and Pi-hole dnsmasq log parsers for the `agentmon` DNS anomaly detection system.

## File Structure

Put `# path/to/file.py` as the first line in each code block. Produce these files:

- `agentmon/collectors/__init__.py` (empty)
- `agentmon/collectors/syslog_receiver.py`
- `agentmon/collectors/syslog_parsers.py`

## Existing Models (already implemented, do NOT rewrite)

`agentmon/models/events.py` already defines:
- `DNSEvent(timestamp, client, domain, query_type, blocked)` — frozen dataclass
- `ConnectionEvent(timestamp, client, src_port, dst_ip, dst_port, protocol)` — dataclass

Import them as: `from agentmon.models.events import DNSEvent, ConnectionEvent`

## Module: `agentmon/collectors/syslog_receiver.py`

### `SyslogMessage` (dataclass)
- Fields: `timestamp` (datetime), `hostname` (str), `tag` (str), `message` (str)
- Optional fields: `facility` (int, default 0), `severity` (int, default 0)

### `SyslogConfig` (dataclass)
- Fields: `port` (int), `protocol` (str — "tcp" or "udp"), `bind_address` (str, default "0.0.0.0")
- Optional: `allowed_ips` (list[str], default None — None means allow all)

### `parse_syslog_message(raw: str) -> SyslogMessage | None`
Free function that parses a raw syslog line.

**RFC 3164 format**: `<PRI>Mon DD HH:MM:SS hostname tag[pid]: message`
- Priority byte: `facility = PRI // 8`, `severity = PRI % 8`
- Example: `<30>Feb 10 12:34:56 pihole dnsmasq[123]: query[A] example.com from 192.168.1.50`

**RFC 5424 format**: `<PRI>1 YYYY-MM-DDTHH:MM:SSZ hostname app_name procid msgid sd message`
- Example: `<30>1 2026-02-10T12:34:56Z pihole dnsmasq 123 - - query[A] test.com from 10.0.0.1`

**Fallback**: If neither format matches, return SyslogMessage with raw text as `message`, hostname="unknown", tag="unknown".

**Oversized messages** (>8192 chars): either truncate or return None. Do not raise.

### `SyslogReceiver`
- `__init__(self, config: SyslogConfig, handler: Callable)`: handler is an async callback taking SyslogMessage
- `is_running` (bool property)
- `async start(self)`: Start listening on config.port
  - For TCP: use `asyncio.start_server`. When a client connects, check allowed_ips. If allowed_ips is set and the client IP is NOT in the list, close connection immediately (don't call handler). Otherwise read lines and call `handler(parse_syslog_message(line))`.
  - For UDP: use `loop.create_datagram_endpoint`. On datagram received, parse and call handler.
- `async stop(self)`: Close server/transport, set is_running=False

## Module: `agentmon/collectors/syslog_parsers.py`

### `PiholeParser`
- `can_parse(self, tag: str) -> bool`: returns True if tag matches any of: "dnsmasq", "dnsmasq-dhcp", "pihole-FTL", "pihole" (case-insensitive)
- `parse(self, msg: SyslogMessage) -> tuple[DNSEvent | None, ConnectionEvent | None]`

Parse the `msg.message` field:

1. **DNS query**: pattern `query[TYPE] DOMAIN from CLIENT`
   - Return `(DNSEvent(timestamp=msg.timestamp, client=CLIENT, domain=DOMAIN, query_type=TYPE, blocked=False), None)`

2. **Blocked with client**: pattern contains "blocked" AND "from" — e.g. `gravity blocked DOMAIN from CLIENT`
   - Return `(DNSEvent(blocked=True, client=CLIENT, domain=DOMAIN, ...), None)`

3. **Blocked without client**: pattern contains "blocked" AND "is" but NOT "from" — e.g. `gravity blocked DOMAIN is 0.0.0.0`
   - Return `(DNSEvent(blocked=True, client="__BLOCK_NOTIFICATION__", domain=DOMAIN, ...), None)`
   - The query_type should default to "A"

4. **Forward/reply lines** (starts with "forwarded" or "reply"): return `(None, None)`

5. **Everything else**: return `(None, None)`

### `route_message(msg: SyslogMessage) -> tuple[DNSEvent | None, ConnectionEvent | None]`
Free function. Instantiate PiholeParser, check `can_parse(msg.tag)`. If yes, return parser.parse(msg). Otherwise return (None, None).
