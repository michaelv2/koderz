from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class Severity(enum.Enum):
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
    client: Optional[str] = None
    domain: Optional[str] = None
    analyzer: Optional[str] = None
    confidence: Optional[float] = None
    llm_analysis: Optional[str] = None
    acknowledged: bool = False
