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
        weighted = self.malicious * 1.0 + self.suspicious * 0.5
        return weighted / total

    @property
    def is_high_risk(self) -> bool:
        return self.malicious >= 5 or self.risk_score > 0.2

    def summary(self) -> str:
        return (
            f"{self.malicious} malicious, {self.suspicious} suspicious, "
            f"{self.undetected} undetected, {self.harmless} harmless"
        )


class VirusTotalClient:
    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key
        self._negative_cache: dict[str, float] = {}

    @property
    def available(self) -> bool:
        return self._api_key is not None and len(self._api_key) > 0

    async def check_domain(self, domain: str) -> Optional[VirusTotalReputation]:
        if not self.available:
            return None
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://www.virustotal.com/api/v3/domains/{domain}",
                headers={"x-apikey": self._api_key},
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            stats = data.get("data", {}).get("attributes", {}).get(
                "last_analysis_stats", {}
            )
            return VirusTotalReputation(
                malicious=stats.get("malicious", 0),
                suspicious=stats.get("suspicious", 0),
                undetected=stats.get("undetected", 0),
                harmless=stats.get("harmless", 0),
            )
