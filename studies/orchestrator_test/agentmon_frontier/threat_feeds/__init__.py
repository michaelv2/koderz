from __future__ import annotations

import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


class ThreatFeedManager:
    def __init__(self, cache_dir: str = "/tmp/agentmon_feeds"):
        self.cache_dir = cache_dir
        self._domains: set[str] = set()

    def _load_cache(self, feed_file: str):
        path = Path(feed_file)
        if not path.exists():
            return
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                parsed = urlparse(line)
                host = parsed.hostname
                if host and not _is_ip(host):
                    self._domains.add(host)
            except Exception:
                continue

    def get_malicious_domains(self) -> set[str]:
        return set(self._domains)

    def check_domain(self, domain: str) -> Optional[str]:
        # Exact match
        if domain in self._domains:
            return domain

        # Check if domain is subdomain of a known-bad domain
        parts = domain.split(".")
        for i in range(1, len(parts)):
            parent = ".".join(parts[i:])
            if parent in self._domains:
                return parent

        return None

    async def update_feeds(self):
        pass


_IP_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


def _is_ip(host: str) -> bool:
    return bool(_IP_RE.match(host))
