from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, List, Optional


@dataclass
class SyslogMessage:
    timestamp: datetime
    hostname: str
    tag: str
    message: str
    facility: int = 0
    severity: int = 0


@dataclass
class SyslogConfig:
    port: int = 514
    protocol: str = "tcp"
    bind_address: str = "0.0.0.0"
    allowed_ips: Optional[List[str]] = None


def _decode_priority(pri: int) -> tuple[int, int]:
    """Decode syslog priority into facility and severity."""
    return pri // 8, pri % 8


_RFC3164_RE = re.compile(
    r"^<(?P<pri>\d+)>(?P<ts>\w{3}\s+\d+\s+\d+:\d+:\d+)\s+"
    r"(?P<hostname>\S+)\s+(?P<tag>\S+?)(?:\[(?P<pid>\d+)\])?:\s*(?P<msg>.*)"
)

_RFC5424_RE = re.compile(
    r"^<(?P<pri>\d+)>1\s+"
    r"(?P<ts>\S+)\s+"
    r"(?P<hostname>\S+)\s+"
    r"(?P<tag>\S+)\s+"
    r"(?P<procid>\S+)\s+"
    r"(?P<msgid>\S+)\s+"
    r"(?P<sd>(?:-|\[.*?\]))\s*"
    r"(?P<msg>.*)"
)


def parse_syslog_message(raw: str) -> Optional[SyslogMessage]:
    if len(raw) > 8192:
        raw = raw[:8192]

    m = _RFC5424_RE.match(raw)
    if m:
        try:
            pri = int(m.group("pri"))
            facility, severity = _decode_priority(pri)
            ts_str = m.group("ts")
            ts = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            hostname = m.group("hostname")
            tag = m.group("tag")
            message = m.group("msg")
            return SyslogMessage(
                timestamp=ts,
                hostname=hostname,
                tag=tag,
                message=message,
                facility=facility,
                severity=severity,
            )
        except Exception as exc:
            logging.debug("RFC5424 parsing failed: %s", exc)

    m = _RFC3164_RE.match(raw)
    if m:
        try:
            pri = int(m.group("pri"))
            facility, severity = _decode_priority(pri)
            ts_str = m.group("ts")
            now = datetime.now(timezone.utc)
            ts = datetime.strptime(ts_str, "%b %d %H:%M:%S").replace(
                year=now.year, tzinfo=timezone.utc
            )
            hostname = m.group("hostname")
            tag = m.group("tag")
            message = m.group("msg")
            return SyslogMessage(
                timestamp=ts,
                hostname=hostname,
                tag=tag,
                message=message,
                facility=facility,
                severity=severity,
            )
        except Exception as exc:
            logging.debug("RFC3164 parsing failed: %s", exc)

    return SyslogMessage(
        timestamp=datetime.now(timezone.utc),
        hostname="unknown",
        tag="raw",
        message=raw,
    )


class _UDPProtocol(asyncio.DatagramProtocol):
    def __init__(
        self,
        handler: Callable[[SyslogMessage], Coroutine[Any, Any, None]],
        allowed_ips: Optional[List[str]] = None,
    ) -> None:
        self._handler = handler
        self._allowed_ips = allowed_ips

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        ip = addr[0]
        if self._allowed_ips is not None and ip not in self._allowed_ips:
            return
        try:
            raw = data.decode(errors="ignore").strip()
            msg = parse_syslog_message(raw)
            if msg:
                asyncio.get_event_loop().create_task(self._handler(msg))
        except Exception as exc:
            logging.exception("Error handling UDP datagram from %s: %s", addr, exc)


class SyslogReceiver:
    def __init__(self, config: SyslogConfig, handler: Callable[[SyslogMessage], Coroutine[Any, Any, None]]) -> None:
        self.config = config
        self.handler = handler
        self.is_running = False
        self._server: Optional[asyncio.AbstractServer] = None
        self._transport: Optional[asyncio.DatagramTransport] = None

    async def start(self) -> None:
        if self.is_running:
            return
        proto = self.config.protocol.lower()
        if proto == "tcp":
            self._server = await asyncio.start_server(
                self._handle_tcp_client,
                host=self.config.bind_address,
                port=self.config.port,
            )
        elif proto == "udp":
            loop = asyncio.get_running_loop()
            self._transport, _ = await loop.create_datagram_endpoint(
                lambda: _UDPProtocol(self.handler, self.config.allowed_ips),
                local_addr=(self.config.bind_address, self.config.port),
            )
        else:
            raise ValueError(f"Unsupported protocol: {self.config.protocol}")
        self.is_running = True

    async def stop(self) -> None:
        if not self.is_running:
            return
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
        peername = writer.get_extra_info("peername")
        client_ip = peername[0] if peername else "unknown"
        if self.config.allowed_ips is not None and client_ip not in self.config.allowed_ips:
            writer.close()
            await writer.wait_closed()
            return

        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                raw = line.decode(errors="ignore").strip()
                msg = parse_syslog_message(raw)
                if msg:
                    try:
                        await self.handler(msg)
                    except Exception as exc:
                        logging.exception("Handler error for message from %s: %s", client_ip, exc)
        except Exception as exc:
            logging.exception("Error handling TCP client %s: %s", client_ip, exc)
        finally:
            writer.close()
            await writer.wait_closed()
