from __future__ import annotations
import socket
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ResolverConfig:
    enabled: bool = True
    strip_suffix: bool = False
    mappings: Dict[str, str] = field(default_factory=dict)


class ClientResolver:
    def __init__(self, config: ResolverConfig):
        self.config = config
        self._cache: Dict[str, str] = {}

    def resolve(self, ip: str) -> str:
        if not self.config.enabled:
            return ip

        # Explicit mapping
        if ip in self.config.mappings:
            hostname = self.config.mappings[ip]
            if self.config.strip_suffix:
                hostname = hostname.split(".")[0]
            return hostname

        # Cache lookup
        if ip in self._cache:
            return self._cache[ip]

        # Reverse DNS lookup
        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
        except Exception:
            hostname = ip

        if self.config.strip_suffix:
            hostname = hostname.split(".")[0]

        self._cache[ip] = hostname
        return hostname

    def get_cache_stats(self) -> Dict[str, int]:
        return {"mappings": len(self.config.mappings), "cached": len(self._cache)}
