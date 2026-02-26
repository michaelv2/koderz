from __future__ import annotations

import math
import re
from collections import Counter

_COMMON_TLDS = {
    "com", "net", "org", "io", "co", "uk", "de", "ru", "cn", "br",
    "fr", "it", "nl", "au", "ca", "in", "jp", "pl", "es", "se",
    "ch", "be", "at", "info", "biz", "us", "tv", "me", "cc", "xyz",
    "top", "site", "online", "club", "app", "dev",
}

_VOWELS = set("aeiouAEIOU")
_CONSONANTS = set("bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ")


def calculate_entropy(s: str) -> float:
    if not s:
        return 0.0
    length = len(s)
    counts = Counter(s)
    entropy = 0.0
    for count in counts.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def calculate_domain_entropy(domain: str) -> float:
    parts = domain.split(".")
    # Strip common TLDs
    while parts and parts[-1].lower() in _COMMON_TLDS:
        parts = parts[:-1]
    if not parts:
        # All parts were TLDs, use original domain minus last part
        parts = domain.split(".")[:-1]
    label = ".".join(parts)
    return calculate_entropy(label)


def is_high_entropy_domain(
    domain: str, threshold: float = 3.5, min_length: int = 8
) -> tuple[bool, float]:
    parts = domain.split(".")
    # Get the main label (everything except TLD)
    while parts and parts[-1].lower() in _COMMON_TLDS:
        parts = parts[:-1]
    if not parts:
        parts = domain.split(".")[:-1]
    label = ".".join(parts)

    if len(label) < min_length:
        return (False, calculate_entropy(label))

    entropy = calculate_entropy(label)
    return (entropy > threshold, entropy)


def has_excessive_consonants(domain: str, threshold: float = 0.65) -> bool:
    parts = domain.split(".")
    # Use the first label (subdomain)
    label = parts[0] if parts else domain
    # Remove hyphens and digits for analysis
    alpha_only = re.sub(r"[^a-zA-Z]", "", label)
    if len(alpha_only) < 4:
        return False
    consonant_count = sum(1 for c in alpha_only if c in _CONSONANTS)
    ratio = consonant_count / len(alpha_only)
    return ratio > threshold


def _has_long_alphanumeric_run(label: str, min_run: int = 12) -> bool:
    clean = label.replace("-", "").replace(".", "")
    run = 0
    for c in clean:
        if c.isalnum():
            run += 1
            if run >= min_run:
                return True
        else:
            run = 0
    return False


def _has_alternating_pattern(label: str) -> bool:
    clean = re.sub(r"[^a-zA-Z0-9]", "", label)
    if len(clean) < 8:
        return False
    alternations = 0
    for i in range(1, len(clean)):
        prev_is_digit = clean[i - 1].isdigit()
        curr_is_digit = clean[i].isdigit()
        if prev_is_digit != curr_is_digit:
            alternations += 1
    ratio = alternations / (len(clean) - 1)
    return ratio > 0.6


def _has_no_vowels(label: str) -> bool:
    alpha_only = re.sub(r"[^a-zA-Z]", "", label)
    if len(alpha_only) < 6:
        return False
    return not any(c in _VOWELS for c in alpha_only)


def looks_like_dga(domain: str) -> tuple[bool, list[str]]:
    parts = domain.split(".")
    # Get the main label(s) minus TLD
    non_tld = []
    for p in parts:
        if p.lower() not in _COMMON_TLDS:
            non_tld.append(p)
    if not non_tld:
        non_tld = parts[:-1] if len(parts) > 1 else parts

    label = ".".join(non_tld)
    reasons = []

    # Signal 1: High entropy
    entropy = calculate_entropy(label)
    if entropy > 3.5 and len(label) >= 8:
        reasons.append(f"high entropy ({entropy:.2f})")

    # Signal 2: Excessive consonants
    if has_excessive_consonants(domain):
        reasons.append("excessive consonant ratio")

    # Signal 3: Long alphanumeric run
    if _has_long_alphanumeric_run(label):
        reasons.append("long alphanumeric run")

    # Signal 4: Alternating pattern (letters/digits)
    if _has_alternating_pattern(label):
        reasons.append("alternating letter/digit pattern")

    # Signal 5: No vowels in long label
    if _has_no_vowels(label):
        reasons.append("no vowels in label")

    is_dga = len(reasons) >= 2
    return (is_dga, reasons)
