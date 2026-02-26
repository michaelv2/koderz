# Subtask 2: Syslog Receiver + Parsers

Implement TWO Python files. Output them as TWO separate fenced code blocks, clearly labeled with their file paths.

## File 1: `agentmon/collectors/syslog_receiver.py`

### Imports
```python
from __future__ import annotations
import asyncio
import re
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Callable, Coroutine, List
```

### `SyslogMessage` dataclass (NOT frozen, regular dataclass)
Fields:
- `timestamp`: datetime
- `hostname`: str
- `tag`: str
- `message`: str
- `facility`: int = 0
- `severity`: int = 0

### `SyslogConfig` dataclass
Fields:
- `port`: int = 514
- `protocol`: str = "tcp"
- `bind_address`: str = "0.0.0.0"
- `allowed_ips`: Optional[List[str]] = None

### `parse_syslog_message(raw: str) -> Optional[SyslogMessage]` (module-level function)

Parse a raw syslog string. Must handle:

1. **RFC 3164**: `<PRI>Mon DD HH:MM:SS hostname tag[pid]: message`
   - Example: `<30>Feb 10 12:34:56 pihole dnsmasq[123]: query[A] example.com from 192.168.1.50`
   - Priority: `<30>` means facility=3 (30//8), severity=6 (30%8)

2. **RFC 5424**: `<PRI>1 YYYY-MM-DDTHH:MM:SSZ hostname appname procid msgid SD message`
   - Example: `<30>1 2026-02-10T12:34:56Z pihole dnsmasq 123 - - query[A] test.com from 10.0.0.1`
   - Detect by `<PRI>1 ` prefix (version digit after priority)

3. **Fallback**: If neither format matches, create a SyslogMessage with:
   - `timestamp=datetime.now(timezone.utc)`, `hostname="unknown"`, `tag="raw"`, `message=raw`

Priority decoding helper `_decode_priority(pri: int) -> tuple[int, int]`:
- facility = pri // 8
- severity = pri % 8

Parsing approach for RFC 3164:
- Use regex: `r'^<(\d+)>(\w{3}\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\S+?)(?:\[(\d+)\])?:\s*(.*)'`
- Extract priority, timestamp_str, hostname, tag, pid, message
- For timestamp, use `datetime.strptime` with `"%b %d %H:%M:%S"` and set year to current year

Parsing approach for RFC 5424:
- Use regex: `r'^<(\d+)>1\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(?:-|(?:\[.*?\]))\s*(.*)'`
- Extract priority, timestamp, hostname, appname, procid, msgid, message
- tag = appname

Oversized messages (>8192 chars): truncate the raw string before parsing, or just parse normally and let it work.

### `SyslogReceiver` class

Constructor: `__init__(self, config: SyslogConfig, handler: Callable)`
- `self.config = config`
- `self.handler = handler`
- `self.is_running = False`
- `self._server = None`  (for TCP)
- `self._transport = None`  (for UDP)

#### `async start(self)`
Based on config.protocol:
- **TCP**: Use `asyncio.start_server` to listen on bind_address:port
  - For each client connection, spawn `_handle_tcp_client(reader, writer)`
- **UDP**: Use `loop.create_datagram_endpoint` with a custom `_UDPProtocol`
- Set `self.is_running = True`

#### `async stop(self)`
- Close the server/transport
- Set `self.is_running = False`

#### `async _handle_tcp_client(self, reader, writer)`
- Get client IP from `writer.get_extra_info('peername')`
- If allowed_ips is set and client IP not in allowed_ips, close connection and return
- Read lines from reader using `reader.readline()`
- For each line, call `parse_syslog_message(line.decode().strip())`
- If parsed, call `await self.handler(msg)`
- Handle connection close/errors gracefully

### `_UDPProtocol` class (asyncio.DatagramProtocol)
- Constructor takes handler function and optional allowed_ips
- `datagram_received(data, addr)`:
  - If allowed_ips set and addr[0] not in allowed_ips, return
  - Parse the data, call handler via `asyncio.ensure_future(handler(msg))`

Important for UDP: The handler is a coroutine, so in `datagram_received` (which is sync), you must schedule it with `asyncio.ensure_future()` or `asyncio.get_event_loop().create_task()`.

## File 2: `agentmon/collectors/syslog_parsers.py`

### Imports
```python
from __future__ import annotations
import re
from datetime import datetime, timezone
from typing import Optional, Tuple
from agentmon.models.events import DNSEvent, ConnectionEvent
from agentmon.collectors.syslog_receiver import SyslogMessage
```

### Regex patterns
```python
_QUERY_RE = re.compile(r'query\[(\w+)\]\s+(\S+)\s+from\s+(\S+)')
_BLOCK_WITH_CLIENT_RE = re.compile(r'(?:gravity\s+)?blocked\s+(\S+)\s+from\s+(\S+)')
_BLOCK_WITHOUT_CLIENT_RE = re.compile(r'(?:gravity\s+)?blocked\s+(\S+)\s+is\s+(\S+)')
```

### `PiholeParser` class

#### `can_parse(self, tag: str) -> bool`
Return True if tag (case-insensitive) contains any of: "dnsmasq", "pihole-ftl", "pihole"

#### `parse(self, msg: SyslogMessage) -> Tuple[Optional[DNSEvent], Optional[ConnectionEvent]]`
1. Check `_QUERY_RE` match on msg.message:
   - If match: create DNSEvent with query_type=group(1), domain=group(2), client=group(3), blocked=False, timestamp=msg.timestamp
   - Return (dns_event, None)

2. Check `_BLOCK_WITH_CLIENT_RE` match on msg.message:
   - IMPORTANT: Only match if it has "from" (not "is") — the "from" pattern means it has a client
   - If match: create DNSEvent with domain=group(1), client=group(2), blocked=True
   - Return (dns_event, None)

3. Check `_BLOCK_WITHOUT_CLIENT_RE` match on msg.message:
   - If match: create DNSEvent with domain=group(1), client="__BLOCK_NOTIFICATION__", blocked=True
   - Return (dns_event, None)

4. For "forwarded" or "reply" lines: Return (None, None)
5. Default: Return (None, None)

IMPORTANT: The BLOCK_WITH_CLIENT regex must match "blocked X from Y" but NOT "blocked X is Y". The BLOCK_WITHOUT_CLIENT regex matches "blocked X is Y". Make sure the regexes are tried in correct order: query first, then block-with-client, then block-without-client.

### `route_message(msg: SyslogMessage) -> Tuple[Optional[DNSEvent], Optional[ConnectionEvent]]`
Module-level function:
- Create list of parsers: `[PiholeParser()]`
- For each parser, check `can_parse(msg.tag)`, if True, return `parser.parse(msg)`
- Default return: `(None, None)`
