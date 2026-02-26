import socket
from dataclasses import dataclass, field


@dataclass
class ResolverConfig:
    enabled: bool = True
    mappings: dict = field(default_factory=dict)
    strip_suffix: bool = False


class ClientResolver:
    def __init__(self, config: ResolverConfig):
        self.config = config
        self._cache = {}

    def resolve(self, ip: str) -> str:
        if not self.config.enabled:
            return ip

        if ip in self._cache:
            return self._cache[ip]

        if ip in self.config.mappings:
            hostname = self.config.mappings[ip]
            if self.config.strip_suffix and "." in hostname:
                hostname = hostname.split(".")[0]
            self._cache[ip] = hostname
            return hostname

        try:
            hostname = socket.gethostbyaddr(ip)[0]
            if self.config.strip_suffix and "." in hostname:
                hostname = hostname.split(".")[0]
            self._cache[ip] = hostname
            return hostname
        except (socket.herror, socket.gaierror, OSError):
            self._cache[ip] = ip
            return ip

    def get_cache_stats(self) -> dict:
        return {
            "mappings": len(self.config.mappings),
            "cached": len(self._cache),
        }
