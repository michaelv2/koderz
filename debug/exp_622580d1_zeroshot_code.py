from typing import List

def separate_paren_groups(paren_string: str) -> List[str]:
    depth = 0
    current = []
    groups = []
    for ch in paren_string:
        if ch == ' ':
            continue
        if ch not in '()':
            continue
        if ch == '(':
            depth += 1
            current.append(ch)
        else:  # ch == ')'
            current.append(ch)
            depth -= 1
        if depth == 0 and current:
            groups.append(''.join(current))
            current = []
    return groups