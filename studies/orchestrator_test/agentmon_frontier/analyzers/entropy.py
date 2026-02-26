from __future__ import annotations

import math
import re
from collections import Counter

# Common TLDs to strip when computing domain entropy
_COMMON_TLDS = {
    "com", "net", "org", "io", "co", "uk", "de", "fr", "jp", "ru",
    "edu", "gov", "mil", "int", "info", "biz", "name", "pro", "xyz",
    "online", "site", "tech", "store", "app", "dev", "cloud",
}

_VOWELS = set("aeiouAEIOU")
_MIN_DOMAIN_LENGTH_FOR_ENTROPY = 6
_HIGH_ENTROPY_THRESHOLD = 3.5
_CONSONANT_RATIO_THRESHOLD = 0.75
_LONG_ALPHANUMERIC_RE = re.compile(r"[a-z0-9]{12,}", re.IGNORECASE)
_ALTERNATING_RE = re.compile(r"(?:[bcdfghjklmnpqrstvwxyz][0-9]){3,}", re.IGNORECASE)


def calculate_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    length = len(s)
    entropy = 0.0
    for count in counts.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def _strip_tld(domain: str) -> str:
    parts = domain.split(".")
    while len(parts) > 1 and parts[-1].lower() in _COMMON_TLDS:
        parts.pop()
    return ".".join(parts)


def calculate_domain_entropy(domain: str) -> float:
    stripped = _strip_tld(domain)
    # Remove dots for entropy calculation
    label = stripped.replace(".", "")
    return calculate_entropy(label)


def is_high_entropy_domain(domain: str) -> tuple[bool, float]:
    stripped = _strip_tld(domain)
    label = stripped.replace(".", "")
    if len(label) < _MIN_DOMAIN_LENGTH_FOR_ENTROPY:
        return False, 0.0
    entropy = calculate_entropy(label)
    return entropy > _HIGH_ENTROPY_THRESHOLD, entropy


def has_excessive_consonants(domain: str) -> bool:
    stripped = _strip_tld(domain)
    label = stripped.replace(".", "").replace("-", "")
    if len(label) < 4:
        return False
    alpha_chars = [c for c in label if c.isalpha()]
    if not alpha_chars:
        return False
    consonants = [c for c in alpha_chars if c.lower() not in _VOWELS]
    ratio = len(consonants) / len(alpha_chars)
    return ratio >= _CONSONANT_RATIO_THRESHOLD


def _has_no_vowels(label: str) -> bool:
    alpha = [c for c in label if c.isalpha()]
    if len(alpha) < 5:
        return False
    return not any(c.lower() in _VOWELS for c in alpha)


def _has_long_alphanumeric(domain: str) -> bool:
    stripped = _strip_tld(domain)
    return bool(_LONG_ALPHANUMERIC_RE.search(stripped))


def _has_alternating_pattern(domain: str) -> bool:
    stripped = _strip_tld(domain)
    return bool(_ALTERNATING_RE.search(stripped))


def looks_like_dga(domain: str) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    stripped = _strip_tld(domain)
    label = stripped.replace(".", "")

    # Signal 1: high entropy
    high_ent, entropy = is_high_entropy_domain(domain)
    if high_ent:
        reasons.append(f"high entropy ({entropy:.2f})")

    # Signal 2: excessive consonants
    if has_excessive_consonants(domain):
        reasons.append("excessive consonant ratio")

    # Signal 3: long alphanumeric run
    if _has_long_alphanumeric(domain):
        reasons.append("long alphanumeric sequence")

    # Signal 4: alternating consonant-digit pattern
    if _has_alternating_pattern(domain):
        reasons.append("alternating consonant-digit pattern")

    # Signal 5: no vowels at all
    if _has_no_vowels(label):
        reasons.append("no vowels in label")

    # DGA requires at least 2 signals
    is_dga = len(reasons) >= 2
    return is_dga, reasons
