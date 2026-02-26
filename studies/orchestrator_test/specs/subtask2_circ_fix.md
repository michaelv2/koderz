# Fix: Circular Import in Syslog Modules

The current code has a circular import: `syslog_receiver.py` imports from `syslog_parsers.py` and `syslog_parsers.py` imports from `syslog_receiver.py`.

## Fix Required

**`syslog_receiver.py` must NOT import from `syslog_parsers.py`**. It should be self-contained with `SyslogMessage`, `SyslogConfig`, `parse_syslog_message`, and `SyslogReceiver`.

**`syslog_parsers.py` imports `SyslogMessage` from `syslog_receiver.py`** — this is the only allowed cross-import direction.

Rewrite both files completely. Put `# agentmon/collectors/syslog_receiver.py` as the first line in the first code block and `# agentmon/collectors/syslog_parsers.py` as the first line in the second code block.

## `agentmon/collectors/syslog_receiver.py`

Must contain:
- `SyslogMessage` dataclass: fields `timestamp` (datetime), `hostname` (str), `tag` (str), `message` (str), `facility` (int, default 0), `severity` (int, default 0)
- `SyslogConfig` dataclass: fields `port` (int), `protocol` (str), `bind_address` (str, default "0.0.0.0"), `allowed_ips` (list[str] | None, default None)
- `parse_syslog_message(raw: str) -> SyslogMessage | None` function:
  - If raw length > 8192: return None
  - Try RFC 3164: regex `<(\d+)>(\w{3}\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\S+?)(?:\[(\d+)\])?:\s*(.*)` — extract priority, timestamp, hostname, tag, message. Compute facility=priority//8, severity=priority%8
  - Try RFC 5424: regex `<(\d+)>1\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(?:\S+\s+)?(.*)` — extract priority, timestamp, hostname, app_name (as tag), message
  - Fallback: return SyslogMessage with timestamp=now(UTC), hostname="unknown", tag="unknown", message=raw
- `SyslogReceiver` class:
  - `__init__(self, config: SyslogConfig, handler)`: handler is async callable taking SyslogMessage
  - `is_running` property (bool)
  - `async start()`: if protocol=="tcp", use `asyncio.start_server`. If protocol=="udp", use `loop.create_datagram_endpoint` with a custom DatagramProtocol
  - TCP: for each client, check allowed_ips (if set, only allow clients whose IP is in the list; otherwise close connection). Read lines, parse, call handler
  - UDP: create a DatagramProtocol subclass that calls handler on each datagram
  - `async stop()`: close server/transport, set running to False

**No imports from syslog_parsers.**

## `agentmon/collectors/syslog_parsers.py`

Must contain:
- Import `SyslogMessage` from `agentmon.collectors.syslog_receiver`
- Import `DNSEvent, ConnectionEvent` from `agentmon.models.events`
- `PiholeParser` class:
  - `can_parse(self, tag: str) -> bool`: return True if tag.lower() in {"dnsmasq", "dnsmasq-dhcp", "pihole-ftl", "pihole"}
  - `parse(self, msg: SyslogMessage) -> tuple[DNSEvent | None, ConnectionEvent | None]`:
    - Check for `query[TYPE] DOMAIN from CLIENT` pattern → DNSEvent(blocked=False)
    - Check for "blocked" + "from" → DNSEvent(blocked=True, client=CLIENT)
    - Check for "blocked" + "is" (but no "from") → DNSEvent(blocked=True, client="__BLOCK_NOTIFICATION__", query_type="A")
    - Lines starting with "forwarded" or "reply" → (None, None)
    - Anything else → (None, None)
- `route_message(msg: SyslogMessage) -> tuple[DNSEvent | None, ConnectionEvent | None]`:
  - Create PiholeParser, check can_parse(msg.tag), if yes return parser.parse(msg), else return (None, None)
