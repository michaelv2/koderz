from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Set
from urllib.parse import urlparse


def _is_ip(host: str) -> bool:
    return bool(re.fullmatch(r'\d{1,3}(?:\.\d{1,3}){3}', host))


class ThreatFeedManager:
    def __init__(self, cache_dir: str = "/tmp/agentmon_feeds"):
        self.cache_dir = cache_dir
        self._domains: Set[str] = set()

    def get_malicious_domains(self) -> Set[str]:
        return set(self._domains)

    def _load_cache(self, feed_file: str) -> None:
        path = Path(feed_file)
        if not path.is_file():
            return
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parsed = urlparse(line)
                host = parsed.hostname
                if host and not _is_ip(host):
                    self._domains.add(host.lower())

    def check_domain(self, domain: str) -> Optional[str]:
        domain = domain.lower()
        if domain in self._domains:
            return domain
        parts = domain.split(".")
        for i in range(len(parts) - 1):
            parent = ".".join(parts[i + 1:])
            if parent in self._domains:
                return parent
        return None

    async def update_feeds(self) -> None:
        pass
