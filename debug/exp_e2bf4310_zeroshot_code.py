from typing import List

def separate_paren_groups(paren_string: str) -> List[str]:
    s = paren_string.replace(' ', '')
    result: List[str] = []
    depth = 0
    current: List[str] = []
    for ch in s:
        if ch == '(':
            if depth == 0:
                current = []
            depth += 1
            current.append(ch)
        elif ch == ')':
            depth -= 1
            current.append(ch)
            if depth == 0:
                result.append(''.join(current))
        # If there are any other characters (after spaces removal), they are ignored
    return result