# Subtask 2: Syslog Receiver + Parsers

Implement TWO Python files for syslog message reception and parsing.

## File 1: `agentmon/collectors/syslog_receiver.py`

### `SyslogMessage` dataclass
```python
from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class SyslogMessage:
    timestamp: datetime
    hostname: str = ""
    tag: str = ""
    message: str = ""
    facility: int = 0
    severity: int = 0
```

### `SyslogConfig` dataclass
```python
@dataclass
class SyslogConfig:
    port: int = 514
    protocol: str = "tcp"  # "tcp" or "udp"
    bind_address: str = "0.0.0.0"
    allowed_ips: list = field(default_factory=list)  # empty means allow all
```

### `parse_syslog_message(raw: str) -> SyslogMessage | None`

Parse a raw syslog string into a SyslogMessage. Must handle:

1. **RFC 3164** format: `<PRI>Mon DD HH:MM:SS hostname tag[pid]: message`
   - Example: `<30>Feb 10 12:34:56 pihole dnsmasq[123]: query[A] example.com from 192.168.1.50`
   - Priority = facility * 8 + severity. PRI=30 means facility=3, severity=6.
   - Extract: hostname, tag (strip PID bracket), message (after `: `)

2. **RFC 5424** format: `<PRI>1 TIMESTAMP hostname app procid msgid SD message`
   - Example: `<30>1 2026-02-10T12:34:56Z pihole dnsmasq 123 - - query[A] test.com from 10.0.0.1`
   - Detect by `<PRI>1 ` prefix (version=1)

3. **Fallback**: If neither format matches, create SyslogMessage with the raw text as `message`

4. **Oversized messages** (>8192 chars): Either truncate or return None, do NOT raise

Key implementation:
```python
import re

def parse_syslog_message(raw: str) -> SyslogMessage | None:
    if len(raw) > 8192:
        raw = raw[:8192]  # truncate rather than error
    
    # Try to extract priority
    pri_match = re.match(r'<(\d{1,3})>', raw)
    if not pri_match:
        # Fallback: no priority
        return SyslogMessage(
            timestamp=datetime.now(timezone.utc),
            message=raw,
        )
    
    pri = int(pri_match.group(1))
    facility = pri >> 3
    severity_val = pri & 0x07
    rest = raw[pri_match.end():]
    
    # Check for RFC 5424 (starts with "1 " after priority)
    if rest.startswith("1 "):
        # Parse RFC 5424: version timestamp hostname app procid msgid sd message
        parts = rest.split(" ", 7)  # split into max 8 parts
        if len(parts) >= 7:
            hostname = parts[2] if len(parts) > 2 else ""
            app = parts[3] if len(parts) > 3 else ""
            message = parts[7] if len(parts) > 7 else ""
            return SyslogMessage(
                timestamp=datetime.now(timezone.utc),
                hostname=hostname,
                tag=app,
                message=message,
                facility=facility,
                severity=severity_val,
            )
    
    # Try RFC 3164: Mon DD HH:MM:SS hostname tag[pid]: message
    rfc3164_re = r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+?)(?:\[\d+\])?:\s*(.*)'
    m = re.match(rfc3164_re, rest)
    if m:
        return SyslogMessage(
            timestamp=datetime.now(timezone.utc),
            hostname=m.group(2),
            tag=m.group(3),
            message=m.group(4),
            facility=facility,
            severity=severity_val,
        )
    
    # Fallback
    return SyslogMessage(
        timestamp=datetime.now(timezone.utc),
        message=rest,
        facility=facility,
        severity=severity_val,
    )
```

### `SyslogReceiver` class

Async TCP/UDP syslog server:

```python
import asyncio

class SyslogReceiver:
    def __init__(self, config: SyslogConfig, handler):
        """handler is an async callable: async def handler(msg: SyslogMessage)"""
        self.config = config
        self.handler = handler
        self.is_running = False
        self._server = None
        self._transport = None

    async def start(self):
        """Start listening on configured port/protocol."""
        if self.config.protocol == "tcp":
            self._server = await asyncio.start_server(
                self._handle_tcp_client,
                self.config.bind_address,
                self.config.port,
            )
        else:  # udp
            loop = asyncio.get_event_loop()
            self._transport, _ = await loop.create_datagram_endpoint(
                lambda: UDPProtocol(self),
                local_addr=(self.config.bind_address, self.config.port),
            )
        self.is_running = True

    async def stop(self):
        """Stop the server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        if self._transport:
            self._transport.close()
        self.is_running = False

    async def _handle_tcp_client(self, reader, writer):
        """Handle a TCP connection. Check allowed_ips if configured."""
        addr = writer.get_extra_info('peername')
        client_ip = addr[0] if addr else None
        
        # If allowed_ips is set, reject connections from non-allowed IPs
        if self.config.allowed_ips and client_ip not in self.config.allowed_ips:
            writer.close()
            await writer.wait_closed()
            return
        
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                raw = data.decode('utf-8', errors='replace').strip()
                if raw:
                    msg = parse_syslog_message(raw)
                    if msg:
                        await self.handler(msg)
        except Exception:
            pass
        finally:
            writer.close()

    async def _handle_udp(self, data: bytes, addr: tuple):
        """Handle a UDP datagram."""
        client_ip = addr[0] if addr else None
        if self.config.allowed_ips and client_ip not in self.config.allowed_ips:
            return
        raw = data.decode('utf-8', errors='replace').strip()
        if raw:
            msg = parse_syslog_message(raw)
            if msg:
                await self.handler(msg)


class UDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, receiver: SyslogReceiver):
        self.receiver = receiver

    def datagram_received(self, data, addr):
        asyncio.ensure_future(self.receiver._handle_udp(data, addr))
```

**CRITICAL TEST REQUIREMENTS**:
- `SyslogReceiver.is_running` is True after start(), False after stop()
- TCP: sends lines ending in `\n`, handler receives parsed SyslogMessage
- UDP: sends datagrams, handler receives parsed SyslogMessage
- IP allowlist: if `allowed_ips` is set, only those IPs are handled. Others get connection closed (TCP) or silently ignored (UDP)
- `parse_syslog_message("<30>Feb 10 12:34:56 pihole dnsmasq[123]: query[A] example.com from 192.168.1.50")` should have hostname="pihole", "dnsmasq" in tag, "example.com" in message
- Priority 30 decodes to facility=3, severity=6
- Malformed text returns SyslogMessage with message containing the text
- Oversized messages (10000+ chars) handled without raising

## File 2: `agentmon/collectors/syslog_parsers.py`

### `PiholeParser` class

```python
import re
from datetime import datetime, timezone
from agentmon.models.events import DNSEvent, ConnectionEvent
from agentmon.collectors.syslog_receiver import SyslogMessage


class PiholeParser:
    TAGS = {"dnsmasq", "dnsmasq-dhcp", "pihole-FTL", "pihole"}

    def can_parse(self, tag: str) -> bool:
        """Return True if this parser handles the given tag."""
        return tag.lower() in {t.lower() for t in self.TAGS}

    def parse(self, msg: SyslogMessage) -> tuple[DNSEvent | None, ConnectionEvent | None]:
        """Parse a Pi-hole/dnsmasq syslog message.
        
        Returns (dns_event, connection_event) - usually one is None.
        
        Patterns to handle:
        1. "query[TYPE] DOMAIN from CLIENT" -> DNSEvent(blocked=False)
        2. "gravity blocked DOMAIN from CLIENT" -> DNSEvent(blocked=True, client=CLIENT)
        3. "gravity blocked DOMAIN is 0.0.0.0" -> DNSEvent(blocked=True, client="__BLOCK_NOTIFICATION__")
        4. "forwarded ..." -> (None, None)
        5. "reply ..." -> (None, None)
        """
        text = msg.message
        
        # Skip forwarded/reply lines
        if text.startswith("forwarded ") or text.startswith("reply "):
            return None, None
        
        # query[TYPE] DOMAIN from CLIENT
        query_match = re.match(r'query\[(\w+)\]\s+(\S+)\s+from\s+(\S+)', text)
        if query_match:
            return DNSEvent(
                timestamp=msg.timestamp,
                client=query_match.group(3),
                domain=query_match.group(2),
                query_type=query_match.group(1),
                blocked=False,
            ), None
        
        # gravity blocked DOMAIN from CLIENT
        block_from_match = re.match(r'gravity blocked\s+(\S+)\s+from\s+(\S+)', text)
        if block_from_match:
            return DNSEvent(
                timestamp=msg.timestamp,
                client=block_from_match.group(2),
                domain=block_from_match.group(1),
                query_type="A",
                blocked=True,
            ), None
        
        # gravity blocked DOMAIN is 0.0.0.0 (no client)
        block_no_client = re.match(r'gravity blocked\s+(\S+)\s+is\s+', text)
        if block_no_client:
            return DNSEvent(
                timestamp=msg.timestamp,
                client="__BLOCK_NOTIFICATION__",
                domain=block_no_client.group(1),
                query_type="A",
                blocked=True,
            ), None
        
        return None, None
```

### `route_message` function

```python
def route_message(msg: SyslogMessage) -> tuple[DNSEvent | None, ConnectionEvent | None]:
    """Route a syslog message to the appropriate parser.
    
    Returns (dns_event, connection_event). If no parser matches, returns (None, None).
    """
    parsers = [PiholeParser()]
    for parser in parsers:
        if parser.can_parse(msg.tag):
            return parser.parse(msg)
    return None, None
```

**TEST REQUIREMENTS for PiholeParser**:
- `can_parse("dnsmasq")` -> True
- `can_parse("dnsmasq-dhcp")` -> True
- `can_parse("pihole-FTL")` -> True
- `can_parse("pihole")` -> True
- `can_parse("kernel")` -> False
- parse of "query[A] example.com from 192.168.1.100" -> dns.domain="example.com", dns.client="192.168.1.100", dns.query_type="A", dns.blocked=False
- parse of "query[AAAA] ..." -> dns.query_type="AAAA"
- parse of "gravity blocked ads.tracker.com from 192.168.1.100" -> dns.blocked=True, dns.client="192.168.1.100"
- parse of "gravity blocked ads.example.com is 0.0.0.0" -> dns.client="__BLOCK_NOTIFICATION__", dns.blocked=True
- parse of "forwarded ..." -> (None, None)
- parse of "reply ..." -> (None, None)

**TEST REQUIREMENTS for route_message**:
- SyslogMessage with tag="dnsmasq" routes to PiholeParser
- SyslogMessage with tag="cron" returns (None, None)

Write COMPLETE, RUNNABLE code for both files. No stubs. Wrap each in ```python blocks with filename as comment.
