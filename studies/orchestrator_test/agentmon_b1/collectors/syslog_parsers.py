from __future__ import annotations

import re
from typing import Optional, Tuple

from agentmon.models.events import DNSEvent, ConnectionEvent
from agentmon.collectors.syslog_receiver import SyslogMessage

_QUERY_RE = re.compile(r"query\[(\w+)\]\s+(\S+)\s+from\s+(\S+)")
_BLOCK_WITH_CLIENT_RE = re.compile(r"(?:gravity\s+)?blocked\s+(\S+)\s+from\s+(\S+)")
_BLOCK_WITHOUT_CLIENT_RE = re.compile(r"(?:gravity\s+)?blocked\s+(\S+)\s+is\s+(\S+)")


class PiholeParser:
    """Parser for Pi-hole / dnsmasq syslog messages."""

    def can_parse(self, tag: str) -> bool:
        tag_lower = tag.lower()
        return any(sub in tag_lower for sub in ("dnsmasq", "pihole-ftl", "pihole"))

    def parse(
        self, msg: SyslogMessage
    ) -> Tuple[Optional[DNSEvent], Optional[ConnectionEvent]]:
        # 1. Query
        m = _QUERY_RE.search(msg.message)
        if m:
            query_type, domain, client = m.groups()
            dns_event = DNSEvent(
                query_type=query_type,
                domain=domain,
                client=client,
                blocked=False,
                timestamp=msg.timestamp,
            )
            return dns_event, None

        # 2. Block with client
        m = _BLOCK_WITH_CLIENT_RE.search(msg.message)
        if m:
            domain, client = m.groups()
            dns_event = DNSEvent(
                query_type="",
                domain=domain,
                client=client,
                blocked=True,
                timestamp=msg.timestamp,
            )
            return dns_event, None

        # 3. Block without client
        m = _BLOCK_WITHOUT_CLIENT_RE.search(msg.message)
        if m:
            domain, _ = m.groups()
            dns_event = DNSEvent(
                query_type="",
                domain=domain,
                client="__BLOCK_NOTIFICATION__",
                blocked=True,
                timestamp=msg.timestamp,
            )
            return dns_event, None

        return None, None


def route_message(msg: SyslogMessage) -> Tuple[Optional[DNSEvent], Optional[ConnectionEvent]]:
    parsers = [PiholeParser()]
    for parser in parsers:
        if parser.can_parse(msg.tag):
            return parser.parse(msg)
    return None, None
