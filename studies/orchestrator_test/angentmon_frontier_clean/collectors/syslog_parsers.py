from __future__ import annotations

import re
from typing import Optional, Tuple

from agentmon.collectors.syslog_receiver import SyslogMessage
from agentmon.models.events import ConnectionEvent, DNSEvent


class PiholeParser:
    _DNSMASQ_TAGS = {"dnsmasq", "dnsmasq-dhcp", "pihole-ftl", "pihole"}

    # query[A] example.com from 192.168.1.100
    _QUERY_RE = re.compile(
        r"query\[(\w+)\]\s+(\S+)\s+from\s+(\S+)"
    )
    # gravity blocked ads.tracker.com from 192.168.1.100
    _BLOCKED_WITH_CLIENT_RE = re.compile(
        r"(?:gravity\s+blocked|\/etc\/pihole\/gravity\.list)\s+(\S+)\s+from\s+(\S+)"
    )
    # gravity blocked ads.example.com is 0.0.0.0
    _BLOCKED_WITHOUT_CLIENT_RE = re.compile(
        r"(?:gravity\s+blocked|\/etc\/pihole\/gravity\.list)\s+(\S+)\s+is\s+(\S+)"
    )

    def can_parse(self, tag: str) -> bool:
        return tag.lower() in self._DNSMASQ_TAGS

    def parse(
        self, msg: SyslogMessage
    ) -> Tuple[Optional[DNSEvent], Optional[ConnectionEvent]]:
        text = msg.message

        # Check query
        m = self._QUERY_RE.search(text)
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

        # Check blocked with client
        m = self._BLOCKED_WITH_CLIENT_RE.search(text)
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

        # Check blocked without client (is 0.0.0.0 / NXDOMAIN response)
        m = self._BLOCKED_WITHOUT_CLIENT_RE.search(text)
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

        return (None, None)


_PARSERS = [PiholeParser()]


def route_message(
    msg: SyslogMessage,
) -> Tuple[Optional[DNSEvent], Optional[ConnectionEvent]]:
    for parser in _PARSERS:
        if parser.can_parse(msg.tag):
            return parser.parse(msg)
    return (None, None)
