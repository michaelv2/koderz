from typing import List

def separate_paren_groups(paren_string: str) -> 'List[str]':
    s = paren_string.replace(" ", "")
    result = []
    depth = 0
    start = None

    for i, ch in enumerate(s):
        if ch == '(':
            if depth == 0:
                start = i
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0 and start is not None:
                result.append(s[start:i + 1])
        else:
            # ignore any other characters, if present
            pass

    return result