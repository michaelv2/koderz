# agentmon/collectors/syslog_receiver.py
"""
Syslog receiver and parser implementation.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Awaitable, Callable, Optional

# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #

@dataclass
class SyslogMessage:
    timestamp: datetime
    hostname: str = ""
    tag: str = ""
    message: str = ""
    facility: int = 0
    severity: int = 0


@dataclass
class SyslogConfig:
    port: int = 514
    protocol: str = "tcp"  # "tcp" or "udp"
    bind_address: str = "0.0.0.0"
    allowed_ips: list[str] = field(default_factory=list)  # empty means allow all


# --------------------------------------------------------------------------- #
# Parsing logic
# --------------------------------------------------------------------------- #

def parse_syslog_message(raw: str) -> Optional[SyslogMessage]:
    """
    Parse a raw syslog string into a SyslogMessage.
    Handles RFC 3164 and RFC 5424 formats.
    """
    # Truncate oversized messages
    if len(raw) > 8192:
        raw = raw[:8192]

    # Extract priority
    pri_match = re.match(r"<(\d{1,3})>", raw)
    if not pri_match:
        # No priority: fallback
        return SyslogMessage(
            timestamp=datetime.now(timezone.utc),
            message=raw,
        )

    pri = int(pri_match.group(1))
    facility = pri >> 3
    severity_val = pri & 0x07
    rest = raw[pri_match.end():]

    # RFC 5424: <PRI>1 TIMESTAMP HOSTNAME APP PROCID MSGID SD MESSAGE
    if rest.startswith("1 "):
        # Split into 8 parts: version, timestamp, hostname, app, procid, msgid, sd, message
        parts = rest.split(" ", 7)
        if len(parts) >= 8:
            _, timestamp_str, hostname, app, procid, msgid, sd, message = parts
            # Parse timestamp if possible
            try:
                ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except Exception:
                ts = datetime.now(timezone.utc)
            return SyslogMessage(
                timestamp=ts,
                hostname=hostname,
                tag=app,
                message=message,
                facility=facility,
                severity=severity_val,
            )
        else:
            # Malformed RFC5424, fallback to raw
            return SyslogMessage(
                timestamp=datetime.now(timezone.utc),
                message=rest,
                facility=facility,
                severity=severity_val,
            )

    # RFC 3164: <PRI>Mon DD HH:MM:SS HOSTNAME TAG[PID]: MESSAGE
    rfc3164_re = r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+?)(?:\[\d+\])?:\s*(.*)"
    m = re.match(rfc3164_re, rest)
    if m:
        # timestamp_str = m.group(1)  # Not used
        hostname = m.group(2)
        tag = m.group(3)
        message = m.group(4)
        return SyslogMessage(
            timestamp=datetime.now(timezone.utc),
            hostname=hostname,
            tag=tag,
            message=message,
            facility=facility,
            severity=severity_val,
        )

    # Fallback: no recognizable format
    return SyslogMessage(
        timestamp=datetime.now(timezone.utc),
        message=rest,
        facility=facility,
        severity=severity_val,
    )


# --------------------------------------------------------------------------- #
# Async syslog receiver
# --------------------------------------------------------------------------- #

class SyslogReceiver:
    """
    Async TCP/UDP syslog server.
    """

    def __init__(self, config: SyslogConfig, handler: Callable[[SyslogMessage], Awaitable[None]]):
        """
        :param config: SyslogConfig instance.
        :param handler: Async callable that receives a SyslogMessage.
        """
        self.config = config
        self.handler = handler
        self.is_running: bool = False
        self._server: Optional[asyncio.AbstractServer] = None
        self._transport: Optional[asyncio.DatagramTransport] = None

    async def start(self) -> None:
        """Start listening on configured port/protocol."""
        if self.config.protocol.lower() == "tcp":
            self._server = await asyncio.start_server(
                self._handle_tcp_client,
                host=self.config.bind_address,
                port=self.config.port,
            )
        else:  # udp
            loop = asyncio.get_running_loop()
            self._transport, _ = await loop.create_datagram_endpoint(
                lambda: UDPProtocol(self),
                local_addr=(self.config.bind_address, self.config.port),
            )
        self.is_running = True

    async def stop(self) -> None:
        """Stop the server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        if self._transport:
            self._transport.close()
            self._transport = None
        self.is_running = False

    async def _handle_tcp_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle a TCP connection."""
        addr = writer.get_extra_info("peername")
        client_ip = addr[0] if addr else None

        # Enforce allowlist
        if self.config.allowed_ips and client_ip not in self.config.allowed_ips:
            writer.close()
            await writer.wait_closed()
            return

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                raw = data.decode("utf-8", errors="replace").strip()
                if raw:
                    msg = parse_syslog_message(raw)
                    if msg:
                        await self.handler(msg)
        except Exception:
            # Silently ignore errors to keep server running
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    async def _handle_udp(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle a UDP datagram."""
        client_ip = addr[0] if addr else None
        if self.config.allowed_ips and client_ip not in self.config.allowed_ips:
            return
        raw = data.decode("utf-8", errors="replace").strip()
        if raw:
            msg = parse_syslog_message(raw)
            if msg:
                await self.handler(msg)


class UDPProtocol(asyncio.DatagramProtocol):
    """
    Datagram protocol that forwards data to SyslogReceiver.
    """

    def __init__(self, receiver: SyslogReceiver):
        self.receiver = receiver

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        asyncio.create_task(self.receiver._handle_udp(data, addr))


# agentmon/collectors/syslog_parsers.py
"""
Pi‑hole / dnsmasq syslog message parsers.
"""

from __future__ import annotations

from typing import Tuple

# Import the event models.  If the real module is not available, provide minimal stubs.
try:
    from agentmon.models.events import DNSEvent, ConnectionEvent
except Exception:  # pragma: no cover
    class DNSEvent:
        def __init__(self, timestamp, client, domain, query_type, blocked):
            self.timestamp = timestamp
            self.client = client
            self.domain = domain
            self.query_type = query_type
            self.blocked = blocked

    class ConnectionEvent:
        pass

from agentmon.collectors.syslog_receiver import SyslogMessage


class PiholeParser:
    """
    Parser for Pi‑hole / dnsmasq syslog messages.
    """

    TAGS = {"dnsmasq", "dnsmasq-dhcp", "pihole-FTL", "pihole"}

    def can_parse(self, tag: str) -> bool:
        """Return True if this parser handles the given tag."""
        return tag.lower() in {t.lower() for t in self.TAGS}

    def parse(
        self, msg: SyslogMessage
    ) -> Tuple[Optional[DNSEvent], Optional[ConnectionEvent]]:
        """Parse a Pi‑hole/dnsmasq syslog message.

        Returns (dns_event, connection_event) – usually one is None.
        """
        text = msg.message.strip()

        # Skip forwarded/reply lines
        if text.startswith("forwarded ") or text.startswith("reply "):
            return None, None

        # query[TYPE] DOMAIN from CLIENT
        query_match = re.match(r"query\[(\w+)\]\s+(\S+)\s+from\s+(\S+)", text)
        if query_match:
            return (
                DNSEvent(
                    timestamp=msg.timestamp,
                    client=query_match.group(3),
                    domain=query_match.group(2),
                    query_type=query_match.group(1),
                    blocked=False,
                ),
                None,
            )

        # gravity blocked DOMAIN from CLIENT
        block_from_match = re.match(r"gravity blocked\s+(\S+)\s+from\s+(\S+)", text)
        if block_from_match:
            return (
                DNSEvent(
                    timestamp=msg.timestamp,
                    client=block_from_match.group(2),
                    domain=block_from_match.group(1),
                    query_type="A",
                    blocked=True,
                ),
                None,
            )

        # gravity blocked DOMAIN is 0.0.0.0 (no client)
        block_no_client = re.match(r"gravity blocked\s+(\S+)\s+is\s+", text)
        if block_no_client:
            return (
                DNSEvent(
                    timestamp=msg.timestamp,
                    client="__BLOCK_NOTIFICATION__",
                    domain=block_no_client.group(1),
                    query_type="A",
                    blocked=True,
                ),
                None,
            )

        return None, None


def route_message(msg: SyslogMessage) -> Tuple[Optional[DNSEvent], Optional[ConnectionEvent]]:
    """Route a syslog message to the appropriate parser.

    Returns (dns_event, connection_event). If no parser matches, returns (None, None).
    """
    parsers = [PiholeParser()]
    for parser in parsers:
        if parser.can_parse(msg.tag):
            return parser.parse(msg)
    return None, None
