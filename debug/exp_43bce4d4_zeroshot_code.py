from typing import List

def separate_paren_groups(paren_string: str) -> List[str]:
    # Keep only parentheses, ignore spaces or any other characters
    filtered = [c for c in paren_string if c in '()']
    s = ''.join(filtered)

    groups: List[str] = []
    balance = 0
    start = None

    for i, ch in enumerate(s):
        if ch == '(':
            if balance == 0:
                start = i
            balance += 1
        elif ch == ')':
            balance -= 1
            if balance == 0 and start is not None:
                groups.append(s[start:i + 1])
                start = None
    return groups