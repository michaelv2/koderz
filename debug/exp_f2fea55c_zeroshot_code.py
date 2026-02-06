def same_chars(s0: str, s1: str):
    from collections import Counter
    return Counter(s0) == Counter(s1)