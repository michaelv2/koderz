from __future__ import annotations

import re
from typing import Optional

from agentmon.collectors.syslog_receiver import SyslogMessage
from agentmon.models.events import ConnectionEvent, DNSEvent

# dnsmasq query: query[A] example.com from 192.168.1.100
_QUERY_RE = re.compile(r"query\[(\w+)\]\s+(\S+)\s+from\s+(\S+)")

# dnsmasq gravity block with client: gravity blocked ads.tracker.com from 192.168.1.100
_BLOCK_WITH_CLIENT_RE = re.compile(r"gravity\s+blocked\s+(\S+)\s+from\s+(\S+)")

# dnsmasq gravity block without client: gravity blocked ads.example.com is 0.0.0.0
_BLOCK_WITHOUT_CLIENT_RE = re.compile(r"gravity\s+blocked\s+(\S+)\s+is\s+(\S+)")

# Lines to ignore
_IGNORE_PREFIXES = ("forwarded", "reply", "cached", "config", "read")

_PIHOLE_TAGS = {"dnsmasq", "dnsmasq-dhcp", "pihole-ftl", "pihole"}


class PiholeParser:
    def can_parse(self, tag: str) -> bool:
        return tag.lower() in _PIHOLE_TAGS

    def parse(
        self, msg: SyslogMessage
    ) -> tuple[Optional[DNSEvent], Optional[ConnectionEvent]]:
        text = msg.message.strip()

        # Check ignore prefixes
        first_word = text.split()[0].lower() if text else ""
        if first_word in _IGNORE_PREFIXES:
            return None, None

        # Try query match
        m = _QUERY_RE.search(text)
        if m:
            return (
                DNSEvent(
                    timestamp=msg.timestamp,
                    client=m.group(3),
                    domain=m.group(2),
                    query_type=m.group(1),
                    blocked=False,
                ),
                None,
            )

        # Try block with client
        m = _BLOCK_WITH_CLIENT_RE.search(text)
        if m:
            return (
                DNSEvent(
                    timestamp=msg.timestamp,
                    client=m.group(2),
                    domain=m.group(1),
                    query_type="A",
                    blocked=True,
                ),
                None,
            )

        # Try block without client
        m = _BLOCK_WITHOUT_CLIENT_RE.search(text)
        if m:
            return (
                DNSEvent(
                    timestamp=msg.timestamp,
                    client="__BLOCK_NOTIFICATION__",
                    domain=m.group(1),
                    query_type="A",
                    blocked=True,
                ),
                None,
            )

        return None, None


_PARSERS = [PiholeParser()]


def route_message(
    msg: SyslogMessage,
) -> tuple[Optional[DNSEvent], Optional[ConnectionEvent]]:
    for parser in _PARSERS:
        if parser.can_parse(msg.tag):
            return parser.parse(msg)
    return None, None
