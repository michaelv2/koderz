from typing import List, Optional

def longest(strings: List[str]) -> Optional[str]:
    if not strings:
        return None
    best = strings[0]
    for s in strings[1:]:
        if len(s) > len(best):
            best = s
    return best