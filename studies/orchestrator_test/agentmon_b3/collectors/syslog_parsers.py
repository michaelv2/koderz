import re
from typing import Tuple, Optional

from agentmon.models.events import DNSEvent, ConnectionEvent
from agentmon.collectors.syslog_receiver import SyslogMessage


class PiholeParser:
    _TAG_SET = {"dnsmasq", "dnsmasq-dhcp", "pihole-ftl", "pihole"}

    @staticmethod
    def can_parse(tag: str) -> bool:
        # Strip PID suffix like "[123]" from tag
        base_tag = re.sub(r"\[\d+\]$", "", tag).lower()
        return base_tag in PiholeParser._TAG_SET

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
