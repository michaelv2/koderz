from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional


@dataclass
class SyslogMessage:
    timestamp: datetime
    hostname: str
    tag: str
    message: str
    facility: Optional[int] = None
    severity: Optional[int] = None


@dataclass
class SyslogConfig:
    port: int = 514
    protocol: str = "tcp"
    bind_address: str = "0.0.0.0"
    allowed_ips: Optional[list[str]] = None
    max_message_size: int = 8192


def parse_syslog_message(raw: str) -> Optional[SyslogMessage]:
    if not raw or not raw.strip():
        return None

    facility = None
    severity_val = None
    rest = raw

    # Parse priority
    pri_match = re.match(r"<(\d+)>", raw)
    if pri_match:
        pri = int(pri_match.group(1))
        facility = pri >> 3
        severity_val = pri & 7
        rest = raw[pri_match.end():]

    now = datetime.now(timezone.utc)

    # Try RFC 5424: starts with version number
    rfc5424_match = re.match(
        r"(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S*)\s*(.*)",
        rest,
    )
    if rfc5424_match:
        hostname = rfc5424_match.group(3)
        app_name = rfc5424_match.group(4)
        msg = rfc5424_match.group(8)
        return SyslogMessage(
            timestamp=now,
            hostname=hostname,
            tag=app_name,
            message=msg,
            facility=facility,
            severity=severity_val,
        )

    # Try RFC 3164: Mon DD HH:MM:SS hostname tag[pid]: message
    rfc3164_match = re.match(
        r"(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+?)(?:\[(\d+)\])?:\s*(.*)",
        rest,
    )
    if rfc3164_match:
        hostname = rfc3164_match.group(2)
        tag = rfc3164_match.group(3)
        msg = rfc3164_match.group(5)
        return SyslogMessage(
            timestamp=now,
            hostname=hostname,
            tag=tag,
            message=msg,
            facility=facility,
            severity=severity_val,
        )

    # Fallback: return raw text
    return SyslogMessage(
        timestamp=datetime.now(timezone.utc),
        hostname="unknown",
        tag="unknown",
        message=raw.strip(),
        facility=facility,
        severity=severity_val,
    )


class SyslogReceiver:
    def __init__(
        self,
        config: SyslogConfig,
        handler: Callable[[SyslogMessage], Awaitable[None]],
    ):
        self.config = config
        self.handler = handler
        self._server = None
        self._transport = None
        self.is_running = False

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

    def _is_ip_allowed(self, ip: str) -> bool:
        if self.config.allowed_ips is None:
            return True
        return ip in self.config.allowed_ips

    async def _handle_tcp_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        peer = writer.get_extra_info("peername")
        peer_ip = peer[0] if peer else "unknown"

        if not self._is_ip_allowed(peer_ip):
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
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _handle_udp_message(self, data: bytes, addr: tuple):
        peer_ip = addr[0]
        if not self._is_ip_allowed(peer_ip):
            return
        raw = data.decode("utf-8", errors="replace").strip()
        if raw:
            msg = parse_syslog_message(raw)
            if msg:
                await self.handler(msg)


class _UDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, receiver: SyslogReceiver):
        self.receiver = receiver

    def datagram_received(self, data: bytes, addr: tuple):
        asyncio.ensure_future(self.receiver._handle_udp_message(data, addr))
