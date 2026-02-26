from __future__ import annotations

import socket
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResolverConfig:
    enabled: bool = True
    strip_suffix: bool = False
    mappings: dict[str, str] = field(default_factory=dict)


class ClientResolver:
    def __init__(self, config: ResolverConfig):
        self.config = config
        self._cache: dict[str, str] = {}

    def resolve(self, ip: str) -> str:
        if not self.config.enabled:
            return ip

        # Check explicit mappings first
        if ip in self.config.mappings:
            name = self.config.mappings[ip]
            if self.config.strip_suffix:
                name = name.split(".")[0]
            return name

        # Check cache
        if ip in self._cache:
            return self._cache[ip]

        # Try reverse DNS
        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            if self.config.strip_suffix:
                hostname = hostname.split(".")[0]
            self._cache[ip] = hostname
            return hostname
        except (socket.herror, socket.gaierror, OSError):
            self._cache[ip] = ip
            return ip

    def get_cache_stats(self) -> dict[str, int]:
        return {
            "mappings": len(self.config.mappings),
            "cache_size": len(self._cache),
        }
