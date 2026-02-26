from __future__ import annotations

import re
from typing import Tuple, Optional

from agentmon.models.events import DNSEvent, ConnectionEvent
from agentmon.collectors.syslog_receiver import SyslogMessage


class PiholeParser:
    TAGS = {"dnsmasq", "dnsmasq-dhcp", "pihole-FTL", "pihole"}

    def can_parse(self, tag: str) -> bool:
        return tag.lower() in {t.lower() for t in self.TAGS}

    def parse(self, msg: SyslogMessage) -> Tuple[Optional[DNSEvent], Optional[ConnectionEvent]]:
        text = msg.message.strip()

        if text.startswith("forwarded ") or text.startswith("reply "):
            return None, None

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
    parsers = [PiholeParser()]
    for parser in parsers:
        if parser.can_parse(msg.tag):
            return parser.parse(msg)
    return None, None
