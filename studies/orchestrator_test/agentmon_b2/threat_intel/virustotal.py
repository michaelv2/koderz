from __future__ import annotations

from dataclasses import dataclass


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
        return self.malicious >= 3 or self.risk_score > 0.2

    def summary(self) -> str:
        total = self.malicious + self.suspicious + self.undetected + self.harmless
        return f"{self.malicious} malicious, {self.suspicious} suspicious out of {total} engines"


class VirusTotalClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    @property
    def available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 0)
