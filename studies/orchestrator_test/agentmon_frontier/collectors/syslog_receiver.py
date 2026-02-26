from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger(__name__)

MAX_MESSAGE_SIZE = 8192


@dataclass
class SyslogMessage:
    timestamp: datetime
    hostname: str
    tag: str = ""
    message: str = ""
    facility: int = 0
    severity: int = 0


@dataclass
class SyslogConfig:
    port: int = 514
    protocol: str = "tcp"
    bind_address: str = "0.0.0.0"
    allowed_ips: Optional[list[str]] = None


# RFC 3164: <PRI>Mmm dd hh:mm:ss HOSTNAME TAG: MSG
_RFC3164_RE = re.compile(
    r"<(\d{1,3})>"
    r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(\S+)\s+"
    r"(\S+?)(?:\[(\d+)\])?:\s*"
    r"(.*)"
)

# RFC 5424: <PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID SD MSG
_RFC5424_RE = re.compile(
    r"<(\d{1,3})>(\d+)\s+"
    r"(\S+)\s+"
    r"(\S+)\s+"
    r"(\S+)\s+"
    r"(\S+)\s+"
    r"(\S+)\s+"
    r"(\S*)\s*"
    r"(.*)"
)


def _decode_priority(pri: int) -> tuple[int, int]:
    facility = pri >> 3
    severity = pri & 0x07
    return facility, severity


def parse_syslog_message(raw: str) -> Optional[SyslogMessage]:
    if len(raw) > MAX_MESSAGE_SIZE:
        raw = raw[:MAX_MESSAGE_SIZE]

    # Try RFC 5424
    m = _RFC5424_RE.match(raw)
    if m:
        pri = int(m.group(1))
        facility, severity = _decode_priority(pri)
        hostname = m.group(4)
        app_name = m.group(5)
        msg = m.group(9)
        try:
            ts = datetime.fromisoformat(m.group(3).replace("Z", "+00:00"))
        except (ValueError, IndexError):
            ts = datetime.now(timezone.utc)
        return SyslogMessage(
            timestamp=ts,
            hostname=hostname,
            tag=app_name,
            message=msg,
            facility=facility,
            severity=severity,
        )

    # Try RFC 3164
    m = _RFC3164_RE.match(raw)
    if m:
        pri = int(m.group(1))
        facility, severity = _decode_priority(pri)
        hostname = m.group(3)
        tag = m.group(4)
        msg = m.group(6)
        try:
            ts_str = m.group(2)
            year = datetime.now().year
            ts = datetime.strptime(f"{year} {ts_str}", "%Y %b %d %H:%M:%S").replace(
                tzinfo=timezone.utc
            )
        except (ValueError, IndexError):
            ts = datetime.now(timezone.utc)
        return SyslogMessage(
            timestamp=ts,
            hostname=hostname,
            tag=tag,
            message=msg,
            facility=facility,
            severity=severity,
        )

    # Fallback: treat as raw text
    return SyslogMessage(
        timestamp=datetime.now(timezone.utc),
        hostname="unknown",
        tag="",
        message=raw,
    )


class SyslogReceiver:
    def __init__(
        self,
        config: SyslogConfig,
        handler: Callable[[SyslogMessage], Coroutine[Any, Any, None]],
    ):
        self.config = config
        self.handler = handler
        self.is_running = False
        self._server = None
        self._transport = None

    async def start(self):
        if self.config.protocol == "tcp":
            self._server = await asyncio.start_server(
                self._handle_tcp_client,
                self.config.bind_address,
                self.config.port,
            )
            self.is_running = True
        elif self.config.protocol == "udp":
            loop = asyncio.get_event_loop()
            self._transport, _ = await loop.create_datagram_endpoint(
                lambda: _UDPProtocol(self),
                local_addr=(self.config.bind_address, self.config.port),
            )
            self.is_running = True

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        if self._transport:
            self._transport.close()
            self._transport = None
        self.is_running = False

    def _is_allowed(self, addr: str) -> bool:
        if self.config.allowed_ips is None:
            return True
        return addr in self.config.allowed_ips

    async def _handle_tcp_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        peername = writer.get_extra_info("peername")
        peer_ip = peername[0] if peername else "unknown"

        if not self._is_allowed(peer_ip):
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
        except (ConnectionError, asyncio.CancelledError):
            pass
        finally:
            writer.close()

    async def _handle_udp_message(self, data: bytes, addr: tuple[str, int]):
        if not self._is_allowed(addr[0]):
            return
        raw = data.decode("utf-8", errors="replace").strip()
        if raw:
            msg = parse_syslog_message(raw)
            if msg:
                await self.handler(msg)


class _UDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, receiver: SyslogReceiver):
        self.receiver = receiver

    def datagram_received(self, data: bytes, addr: tuple[str, int]):
        asyncio.ensure_future(self.receiver._handle_udp_message(data, addr))
