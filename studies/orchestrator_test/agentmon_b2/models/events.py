from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class DNSEvent:
    timestamp: datetime
    client: str
    domain: str
    query_type: str
    blocked: bool

    def domain_parts(self) -> list[str]:
        """Split domain into labels. 'sub.example.co.uk' -> ['sub', 'example', 'co', 'uk']"""
        return self.domain.split(".")


@dataclass(frozen=True)
class ConnectionEvent:
    timestamp: datetime
    client: str
    src_port: int
    dst_ip: str
    dst_port: int
    protocol: str
    bytes_sent: int = 0
    bytes_received: int = 0


@dataclass
class Alert:
    id: str
    timestamp: datetime
    severity: Severity
    title: str
    description: str
    source_event_type: str
    client: str = ""
    domain: str = ""
    analyzer: str = ""
    confidence: float = 0.0
    llm_analysis: str | None = None
    acknowledged: bool = False
