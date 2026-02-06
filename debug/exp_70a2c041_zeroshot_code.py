from typing import List, Optional

def longest(strings: "List[str]") -> "Optional[str]":
    if not strings:
        return None
    best = strings[0]
    max_len = len(best)
    for s in strings[1:]:
        l = len(s)
        if l > max_len:
            best = s
            max_len = l
    return best