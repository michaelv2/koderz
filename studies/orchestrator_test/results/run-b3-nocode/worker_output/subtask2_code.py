# agentmon/collectors/syslog_receiver.py
import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #

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
    port: int
    protocol: str  # "tcp" or "udp"
    bind_address: str = "0.0.0.0"
    allowed_ips: Optional[List[str]] = None


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #

RFC5424_RE = re.compile(
    r"""
    ^<(?P<pri>\d+)>
    (?P<ver>\d+)\s+
    (?P<ts>[^ ]+)\s+
    (?P<host>[^ ]+)\s+
    (?P<app>[^ ]+)\s+
    (?P<proc>[^ ]+)\s+
    (?P<msgid>[^ ]+)\s+
    (?P<sd>[^ ]+)\s+
    (?P<msg>.*)$
    """,
    re.VERBOSE,
)

RFC3164_RE = re.compile(
    r"""
    ^<(?P<pri>\d+)>
    (?P<month>\w{3})\s+
    (?P<day>\d{1,2})\s+
    (?P<time>\d{2}:\d{2}:\d{2})\s+
    (?P<host>[^ ]+)\s+
    (?P<tag>[^:]+):\s+
    (?P<msg>.*)$
    """,
    re.VERBOSE,
)


def _parse_timestamp_rfc5424(ts_str: str) -> datetime:
    # Handle Zulu time
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(ts_str)
    except ValueError:
        # Fallback: ignore timezone
        return datetime.fromisoformat(ts_str.replace("Z", ""))


def _parse_timestamp_rfc3164(month: str, day: str, time_str: str) -> datetime:
    # Use current year; if month/day is in the future, assume previous year
    now = datetime.now()
    ts = datetime.strptime(f"{month} {day} {time_str} {now.year}", "%b %d %H:%M:%S %Y")
    if ts > now:
        ts = ts.replace(year=now.year - 1)
    return ts


def parse_syslog_message(raw: str) -> Optional[SyslogMessage]:
    """
    Parse a raw syslog string into a SyslogMessage.
    Returns None for oversized messages (>8192 chars).
    """
    if len(raw) > 8192:
        return None

    raw = raw.strip()
    if not raw.startswith("<"):
        # Fallback
        return SyslogMessage(
            timestamp=datetime.now(),
            hostname="",
            tag="",
            message=raw,
            facility=0,
            severity=0,
        )

    try:
        pri_end = raw.index(">")
    except ValueError:
        # Malformed
        return SyslogMessage(
            timestamp=datetime.now(),
            hostname="",
            tag="",
            message=raw,
            facility=0,
            severity=0,
        )

    pri_str = raw[1:pri_end]
    try:
        pri = int(pri_str)
    except ValueError:
        pri = 0
    facility = pri // 8
    severity = pri % 8

    rest = raw[pri_end + 1 :].lstrip()

    # Detect RFC5424 by checking if the first token after '>' is a digit
    if rest and rest[0].isdigit() and " " in rest:
        m = RFC5424_RE.match(raw)
        if m:
            ts = _parse_timestamp_rfc5424(m.group("ts"))
            return SyslogMessage(
                timestamp=ts,
                hostname=m.group("host"),
                tag=m.group("app"),
                message=m.group("msg"),
                facility=facility,
                severity=severity,
            )

    # Try RFC3164
    m = RFC3164_RE.match(raw)
    if m:
        ts = _parse_timestamp_rfc3164(m.group("month"), m.group("day"), m.group("time"))
        return SyslogMessage(
            timestamp=ts,
            hostname=m.group("host"),
            tag=m.group("tag"),
            message=m.group("msg"),
            facility=facility,
            severity=severity,
        )

    # Fallback
    return SyslogMessage(
        timestamp=datetime.now(),
        hostname="",
        tag="",
        message=raw,
        facility=facility,
        severity=severity,
    )


# --------------------------------------------------------------------------- #
# SyslogReceiver implementation
# --------------------------------------------------------------------------- #

class _UDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, handler: Callable[[SyslogMessage], None], allowed_ips: Optional[List[str]]):
        self.handler = handler
        self.allowed_ips = allowed_ips

    def datagram_received(self, data: bytes, addr):
        ip, _ = addr
        if self.allowed_ips and ip not in self.allowed_ips:
            return
        raw = data.decode(errors="ignore")
        msg = parse_syslog_message(raw)
        if msg:
            asyncio.create_task(self.handler(msg))


class SyslogReceiver:
    def __init__(self, config: SyslogConfig, handler: Callable[[SyslogMessage], None]):
        self._config = config
        self._handler = handler
        self._tcp_server: Optional[asyncio.AbstractServer] = None
        self._udp_transport: Optional[asyncio.DatagramTransport] = None
        self._udp_protocol: Optional[_UDPProtocol] = None

    @property
    def is_running(self) -> bool:
        if self._config.protocol == "tcp":
            return self._tcp_server is not None and not self._tcp_server.is_closing()
        else:
            return self._udp_transport is not None

    async def _handle_tcp_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        peername = writer.get_extra_info("peername")
        if not peername:
            writer.close()
            await writer.wait_closed()
            return
        ip, _ = peername
        if self._config.allowed_ips and ip not in self._config.allowed_ips:
            writer.close()
            await writer.wait_closed()
            return

        try:
            while not reader.at_eof():
                line = await reader.readline()
                if not line:
                    break
                raw = line.decode(errors="ignore").strip()
                msg = parse_syslog_message(raw)
                if msg:
                    await self._handler(msg)
        except Exception:
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self):
        if self.is_running:
            return

        if self._config.protocol == "tcp":
            self._tcp_server = await asyncio.start_server(
                self._handle_tcp_client,
                host=self._config.bind_address,
                port=self._config.port,
            )
        else:
            loop = asyncio.get_running_loop()
            self._udp_protocol = _UDPProtocol(self._handler, self._config.allowed_ips)
            self._udp_transport, _ = await loop.create_datagram_endpoint(
                lambda: self._udp_protocol,
                local_addr=(self._config.bind_address, self._config.port),
            )

    async def stop(self):
        if self._config.protocol == "tcp" and self._tcp_server:
            self._tcp_server.close()
            await self._tcp_server.wait_closed()
            self._tcp_server = None
        elif self._udp_transport:
            self._udp_transport.close()
            self._udp_transport = None
            self._udp_protocol = None


# agentmon/collectors/syslog_parsers.py
import re
from typing import Optional

from agentmon.models.events import DNSEvent, ConnectionEvent
from agentmon.collectors.syslog_receiver import SyslogMessage


class PiholeParser:
    _TAG_SET = {"dnsmasq", "dnsmasq-dhcp", "pihole-FTL", "pihole"}

    @staticmethod
    def can_parse(tag: str) -> bool:
        return tag.lower() in PiholeParser._TAG_SET

    @staticmethod
    def parse(msg: SyslogMessage) -> Tuple[Optional[DNSEvent], Optional[ConnectionEvent]]:
        text = msg.message.strip()

        # Query pattern
        m = re.match(r"^query\[(?P<type>\w+)\]\s+(?P<domain>\S+)\s+from\s+(?P<client>\S+)$", text)
        if m:
            return (
                DNSEvent(
                    timestamp=msg.timestamp,
                    domain=m.group("domain"),
                    client=m.group("client"),
                    query_type=m.group("type"),
                    blocked=False,
                ),
                None,
            )

        # Gravity blocked with client
        m = re.match(r"^gravity blocked\s+(?P<domain>\S+)\s+from\s+(?P<client>\S+)$", text)
        if m:
            return (
                DNSEvent(
                    timestamp=msg.timestamp,
                    domain=m.group("domain"),
                    client=m.group("client"),
                    query_type="ANY",
                    blocked=True,
                ),
                None,
            )

        # Gravity blocked without client
        m = re.match(r"^gravity blocked\s+(?P<domain>\S+)\s+is\s+0\.0\.0\.0$", text)
        if m:
            return (
                DNSEvent(
                    timestamp=msg.timestamp,
                    domain=m.group("domain"),
                    client="__BLOCK_NOTIFICATION__",
                    query_type="ANY",
                    blocked=True,
                ),
                None,
            )

        # Forwarded or reply messages are ignored
        if text.startswith("forwarded") or text.startswith("reply"):
            return None, None

        return None, None


def route_message(msg: SyslogMessage) -> Tuple[Optional[DNSEvent], Optional[ConnectionEvent]]:
    parsers = [PiholeParser()]
    for parser in parsers:
        if parser.can_parse(msg.tag):
            return parser.parse(msg)
    return None, None
