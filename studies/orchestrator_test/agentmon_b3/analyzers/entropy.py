import math
from collections import Counter
from typing import List, Tuple

VOWELS = set("aeiouAEIOU")


def calculate_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = Counter(s)
    length = len(s)
    entropy = -sum((count / length) * math.log2(count / length) for count in freq.values())
    return entropy


def calculate_domain_entropy(domain: str) -> float:
    parts = domain.split(".")
    if len(parts) > 1:
        domain_without_tld = ".".join(parts[:-1])
    else:
        domain_without_tld = domain
    return calculate_entropy(domain_without_tld)


def is_high_entropy_domain(domain: str) -> Tuple[bool, float]:
    parts = domain.split(".")
    if len(parts) > 1:
        pre_tld = ".".join(parts[:-1])
    else:
        pre_tld = domain
    entropy = calculate_entropy(pre_tld)
    flagged = len(pre_tld) > 6 and entropy > 3.5
    return flagged, entropy


def has_excessive_consonants(domain: str) -> bool:
    parts = domain.split(".")
    if len(parts) > 1:
        pre_tld = ".".join(parts[:-1])
    else:
        pre_tld = domain
    if len(pre_tld) <= 6:
        return False
    consonants = sum(1 for c in pre_tld if c.isalpha() and c not in VOWELS)
    total_letters = sum(1 for c in pre_tld if c.isalpha())
    if total_letters == 0:
        return False
    ratio = consonants / total_letters
    return ratio > 0.7


def _alternating_transition_count(label: str) -> int:
    if not label:
        return 0
    prev_is_digit = label[0].isdigit()
    transitions = 0
    for ch in label[1:]:
        is_digit = ch.isdigit()
        if is_digit != prev_is_digit:
            transitions += 1
            prev_is_digit = is_digit
    return transitions


def looks_like_dga(domain: str) -> Tuple[bool, List[str]]:
    reasons = []

    parts = domain.split(".")
    if len(parts) > 1:
        pre_tld = ".".join(parts[:-1])
    else:
        pre_tld = domain
    if calculate_entropy(pre_tld) > 3.5:
        reasons.append("high_entropy")

    if has_excessive_consonants(domain):
        reasons.append("excessive_consonants")

    for label in parts:
        if len(label) > 15 and label.isalnum():
            reasons.append("long_alphanumeric_label")
            break

    for label in parts:
        if _alternating_transition_count(label) > 5:
            reasons.append("alternating_letters_digits")
            break

    for label in parts:
        if len(label) > 5 and not any(ch in VOWELS for ch in label):
            reasons.append("no_vowels_in_long_label")
            break

    is_dga = len(reasons) >= 2
    return is_dga, reasons
