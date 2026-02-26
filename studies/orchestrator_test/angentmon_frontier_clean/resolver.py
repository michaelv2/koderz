from __future__ import annotations

import socket
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResolverConfig:
    enabled: bool = True
    mappings: Optional[dict[str, str]] = None
    strip_suffix: bool = False


class ClientResolver:
    def __init__(self, config: ResolverConfig):
        self.config = config
        self._mappings: dict[str, str] = config.mappings or {}
        self._cache: dict[str, str] = {}

    def resolve(self, ip: str) -> str:
        if not self.config.enabled:
            return ip

        # Check explicit mappings first
        if ip in self._mappings:
            name = self._mappings[ip]
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

    def get_cache_stats(self) -> dict:
        return {
            "mappings": len(self._mappings),
            "cached": len(self._cache),
        }
