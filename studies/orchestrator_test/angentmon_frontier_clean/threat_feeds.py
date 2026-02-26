from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlparse


class ThreatFeedManager:
    def __init__(self, cache_dir: str = "/tmp/agentmon_feeds"):
        self.cache_dir = cache_dir
        self._malicious_domains: set[str] = set()

    def _load_cache(self, file_path: str):
        try:
            with open(file_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    domain = self._extract_domain(line)
                    if domain:
                        self._malicious_domains.add(domain)
        except FileNotFoundError:
            pass

    def _extract_domain(self, line: str) -> Optional[str]:
        try:
            parsed = urlparse(line)
            hostname = parsed.hostname
            if not hostname:
                return None
            # Skip bare IP addresses
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname):
                return None
            return hostname
        except Exception:
            return None

    def get_malicious_domains(self) -> set[str]:
        return set(self._malicious_domains)

    def check_domain(self, domain: str) -> Optional[str]:
        # Exact match
        if domain in self._malicious_domains:
            return domain
        # Check parent domains (subdomain matching)
        parts = domain.split(".")
        for i in range(1, len(parts)):
            parent = ".".join(parts[i:])
            if parent in self._malicious_domains:
                return parent
        return None

    async def update_feeds(self):
        pass
