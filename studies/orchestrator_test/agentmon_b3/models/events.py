from __future__ import annotations

import dataclasses
import datetime
import enum
from typing import List, Optional


class Severity(enum.Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclasses.dataclass(frozen=True)
class DNSEvent:
    timestamp: datetime.datetime
    client: str
    domain: str
    query_type: str
    blocked: bool

    def domain_parts(self) -> List[str]:
        """Return the domain labels split by '.'."""
        return self.domain.split(".")


@dataclasses.dataclass(frozen=True)
class ConnectionEvent:
    timestamp: datetime.datetime
    client: str
    src_port: int
    dst_ip: str
    dst_port: int
    protocol: str
    bytes_sent: int = 0
    bytes_received: int = 0


@dataclasses.dataclass
class Alert:
    id: str
    timestamp: datetime.datetime
    severity: Severity
    title: str
    description: str
    source_event_type: str
    client: str = ""
    domain: str = ""
    analyzer: str = ""
    confidence: float = 0.0
    llm_analysis: Optional[str] = None
    acknowledged: bool = False
