from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class VirusTotalReputation:
    malicious: int
    suspicious: int
    undetected: int
    harmless: int

    @property
    def risk_score(self) -> float:
        total = self.malicious + self.suspicious + self.undetected + self.harmless
        if total == 0:
            return 0.0
        return (self.malicious * 1.0 + self.suspicious * 0.5) / total

    @property
    def is_high_risk(self) -> bool:
        return self.malicious >= 5 or self.risk_score > 0.2

    def summary(self) -> str:
        return (
            f"{self.malicious} malicious, "
            f"{self.suspicious} suspicious, "
            f"{self.undetected} undetected, "
            f"{self.harmless} harmless"
        )


class VirusTotalClient:
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key

    @property
    def available(self) -> bool:
        return bool(self._api_key and self._api_key.strip())

    async def check_domain(self, domain: str) -> Optional[VirusTotalReputation]:
        if not self.available:
            return None
        return None
