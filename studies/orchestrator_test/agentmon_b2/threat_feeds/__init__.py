from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, Set


class ThreatFeedManager:
    def __init__(self, cache_dir: str = "/tmp/agentmon_feeds"):
        self.cache_dir = Path(cache_dir)
        self._domains: Set[str] = set()

    def _load_cache(self, file_path: str | Path) -> None:
        path = Path(file_path)
        if not path.is_file():
            return
        with path.open() as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    parsed = urlparse(line)
                    hostname = parsed.hostname
                    if hostname and not self._is_ip(hostname):
                        self._domains.add(hostname)
                except Exception:
                    pass

    @staticmethod
    def _is_ip(s: str) -> bool:
        parts = s.split(".")
        if len(parts) == 4:
            try:
                return all(0 <= int(p) <= 255 for p in parts)
            except ValueError:
                return False
        return False

    def get_malicious_domains(self) -> Set[str]:
        return set(self._domains)

    def check_domain(self, domain: str) -> Dict | None:
        if domain in self._domains:
            return {"domain": domain, "source": "threat_feed", "match_type": "exact"}

        parts = domain.split(".")
        for i in range(1, len(parts)):
            parent = ".".join(parts[i:])
            if parent in self._domains:
                return {"domain": parent, "source": "threat_feed", "match_type": "parent"}

        return None
