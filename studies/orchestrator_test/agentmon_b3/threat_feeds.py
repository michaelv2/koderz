import os
import re
import urllib.parse
from typing import Optional, Set


class ThreatFeedManager:
    IP_REGEX = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")

    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        self.malicious_domains: Set[str] = set()

    def _load_cache(self, feed_file: str) -> None:
        path = feed_file if os.path.isabs(feed_file) else os.path.join(self.cache_dir, feed_file)
        if not os.path.isfile(path):
            return

        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parsed = urllib.parse.urlparse(line if "://" in line else f"http://{line}")
                hostname = parsed.hostname or ""
                if not hostname:
                    continue
                if self.IP_REGEX.match(hostname):
                    continue
                self.malicious_domains.add(hostname.lower())

    def get_malicious_domains(self) -> Set[str]:
        return self.malicious_domains

    def check_domain(self, domain: str) -> Optional[str]:
        domain = domain.lower()
        if domain in self.malicious_domains:
            return domain
        parts = domain.split(".")
        for i in range(1, len(parts)):
            parent = ".".join(parts[i:])
            if parent in self.malicious_domains:
                return parent
        return None
