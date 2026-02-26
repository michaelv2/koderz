from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Awaitable, Callable, Optional


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
    protocol: str = "tcp"
    bind_address: str = "0.0.0.0"
    allowed_ips: list[str] = field(default_factory=list)


def parse_syslog_message(raw: str) -> Optional[SyslogMessage]:
    """Parse a raw syslog string into a SyslogMessage."""
    if len(raw) > 8192:
        raw = raw[:8192]

    pri_match = re.match(r"<(\d{1,3})>", raw)
    if not pri_match:
        return SyslogMessage(
            timestamp=datetime.now(timezone.utc),
            message=raw,
        )

    pri = int(pri_match.group(1))
    facility = pri >> 3
    severity_val = pri & 0x07
    rest = raw[pri_match.end():]

    # RFC 5424
    if rest.startswith("1 "):
        parts = rest.split(" ", 7)
        if len(parts) >= 8:
            _, timestamp_str, hostname, app, procid, msgid, sd, message = parts
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
            return SyslogMessage(
                timestamp=datetime.now(timezone.utc),
                message=rest,
                facility=facility,
                severity=severity_val,
            )

    # RFC 3164
    rfc3164_re = r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+?)(?:\[\d+\])?:\s*(.*)"
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


class SyslogReceiver:
    def __init__(self, config: SyslogConfig, handler: Callable[[SyslogMessage], Awaitable[None]]):
        self.config = config
        self.handler = handler
        self.is_running: bool = False
        self._server: Optional[asyncio.AbstractServer] = None
        self._transport: Optional[asyncio.DatagramTransport] = None

    async def start(self) -> None:
        if self.config.protocol.lower() == "tcp":
            self._server = await asyncio.start_server(
                self._handle_tcp_client,
                host=self.config.bind_address,
                port=self.config.port,
            )
        else:
            loop = asyncio.get_running_loop()
            self._transport, _ = await loop.create_datagram_endpoint(
                lambda: UDPProtocol(self),
                local_addr=(self.config.bind_address, self.config.port),
            )
        self.is_running = True

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        if self._transport:
            self._transport.close()
            self._transport = None
        self.is_running = False

    async def _handle_tcp_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        addr = writer.get_extra_info("peername")
        client_ip = addr[0] if addr else None

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
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    async def _handle_udp(self, data: bytes, addr: tuple[str, int]) -> None:
        client_ip = addr[0] if addr else None
        if self.config.allowed_ips and client_ip not in self.config.allowed_ips:
            return
        raw = data.decode("utf-8", errors="replace").strip()
        if raw:
            msg = parse_syslog_message(raw)
            if msg:
                await self.handler(msg)


class UDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, receiver: SyslogReceiver):
        self.receiver = receiver

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        asyncio.create_task(self.receiver._handle_udp(data, addr))
