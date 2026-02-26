import math
from collections import Counter
from typing import Tuple, List


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
    if len(parts) >= 2:
        name_part = ".".join(parts[:-1])
    else:
        name_part = domain
    name_part = name_part.replace(".", "")
    return calculate_entropy(name_part)


def is_high_entropy_domain(domain: str, threshold: float = 3.5) -> Tuple[bool, float]:
    parts = domain.split(".")
    if len(parts) >= 2:
        name_part = ".".join(parts[:-1]).replace(".", "")
    else:
        name_part = domain

    if len(name_part) < 6:
        return False, calculate_domain_entropy(domain)

    entropy = calculate_domain_entropy(domain)
    return entropy > threshold, entropy


def has_excessive_consonants(domain: str) -> bool:
    vowels = set("aeiouAEIOU")
    parts = domain.split(".")
    if len(parts) >= 2:
        name = ".".join(parts[:-1])
    else:
        name = domain
    name = name.replace(".", "").replace("-", "")
    alpha_chars = [c for c in name if c.isalpha()]
    if len(alpha_chars) < 5:
        return False
    consonants = [c for c in alpha_chars if c not in vowels]
    ratio = len(consonants) / len(alpha_chars)
    return ratio > 0.7


def looks_like_dga(domain: str) -> Tuple[bool, List[str]]:
    reasons: List[str] = []

    parts = domain.split(".")
    if len(parts) >= 2:
        name_part = ".".join(parts[:-1]).replace(".", "")
    else:
        name_part = domain

    # Signal 1: high entropy
    flagged, entropy = is_high_entropy_domain(domain)
    if flagged:
        reasons.append(f"high_entropy ({entropy:.2f})")

    # Signal 2: excessive consonants
    if has_excessive_consonants(domain):
        reasons.append("excessive_consonants")

    # Signal 3: long mixed alphanumeric segment
    segments = name_part.split("-")
    for seg in segments:
        if len(seg) > 10:
            has_alpha = any(c.isalpha() for c in seg)
            has_digit = any(c.isdigit() for c in seg)
            if has_alpha and has_digit:
                reasons.append("long_mixed_alphanumeric")
                break

    # Signal 4: alternating letter-digit pattern
    if len(name_part) >= 8:
        alternations = 0
        for i in range(1, len(name_part)):
            prev_is_alpha = name_part[i - 1].isalpha()
            curr_is_alpha = name_part[i].isalpha()
            if prev_is_alpha != curr_is_alpha and name_part[i - 1].isalnum() and name_part[i].isalnum():
                alternations += 1
        if alternations >= 4:
            reasons.append("alternating_pattern")

    # Signal 5: no vowels
    vowels = set("aeiouAEIOU")
    if len(name_part) > 5 and not any(c in vowels for c in name_part):
        reasons.append("no_vowels")

    is_dga = len(reasons) >= 2
    return is_dga, reasons
