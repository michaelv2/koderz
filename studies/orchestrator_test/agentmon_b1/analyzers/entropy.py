from __future__ import annotations

import math
import re
from typing import Tuple, List

_COMMON_TLDS = {
    "com", "net", "org", "io", "co", "uk", "de", "fr", "ru", "cn",
    "jp", "br", "au", "in", "it", "nl", "se", "no", "fi", "dk",
    "info", "biz", "us",
}
_MIN_DOMAIN_LENGTH_FOR_ENTROPY = 6
_HIGH_ENTROPY_THRESHOLD = 3.5
_CONSONANT_RATIO_THRESHOLD = 0.75


def calculate_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(s)
    entropy = 0.0
    for count in freq.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy


def _domain_body(domain: str) -> str:
    labels = domain.lower().split(".")
    if labels and labels[-1] in _COMMON_TLDS:
        labels = labels[:-1]
    return "".join(labels)


def calculate_domain_entropy(domain: str) -> float:
    body = _domain_body(domain)
    return calculate_entropy(body)


def is_high_entropy_domain(domain: str) -> Tuple[bool, float]:
    entropy = calculate_domain_entropy(domain)
    body = _domain_body(domain)
    if len(body) < _MIN_DOMAIN_LENGTH_FOR_ENTROPY:
        return False, entropy
    return entropy > _HIGH_ENTROPY_THRESHOLD, entropy


def has_excessive_consonants(domain: str) -> bool:
    body = _domain_body(domain)
    body_alpha = re.sub(r"[^A-Za-z]", "", body)
    if not body_alpha:
        return False
    consonants = re.sub(r"[aeiouAEIOU]", "", body_alpha)
    ratio = len(consonants) / len(body_alpha)
    return ratio >= _CONSONANT_RATIO_THRESHOLD


def looks_like_dga(domain: str) -> Tuple[bool, List[str]]:
    reasons: List[str] = []

    high_entropy, _ = is_high_entropy_domain(domain)
    if high_entropy:
        reasons.append("high_entropy")

    if has_excessive_consonants(domain):
        reasons.append("excessive_consonants")

    body = _domain_body(domain)

    if re.search(r"[a-zA-Z0-9]{10,}", body):
        reasons.append("long_alphanumeric_run")

    if re.search(r"(?:(?:[bcdfghjklmnpqrstvwxyz][aeiou]){4,})", body, re.IGNORECASE):
        reasons.append("alternating_pattern")

    if not re.search(r"[aeiouAEIOU]", body) and len(body) >= 6:
        reasons.append("no_vowels")

    return len(reasons) >= 2, reasons
