import socket
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ResolverConfig:
    enabled: bool = True
    mappings: Dict[str, str] = field(default_factory=dict)
    strip_suffix: bool = False
    suffix_to_strip: str = ""


class ClientResolver:
    def __init__(self, config: ResolverConfig):
        self.config = config
        self._cache: Dict[str, str] = {}

    def resolve(self, ip: str) -> str:
        if not self.config.enabled:
            return ip

        if ip in self._cache:
            return self._cache[ip]

        hostname: Optional[str] = self.config.mappings.get(ip)

        if hostname is None:
            try:
                hostname, _, _ = socket.gethostbyaddr(ip)
            except Exception:
                hostname = ip

        if self.config.strip_suffix and hostname != ip and "." in hostname:
            hostname = hostname.split(".", 1)[0]

        self._cache[ip] = hostname
        return hostname

    def get_cache_stats(self) -> Dict[str, int]:
        return {"mappings": len(self.config.mappings), "cache_size": len(self._cache)}
