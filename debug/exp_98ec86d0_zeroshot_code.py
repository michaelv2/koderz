from typing import List

def parse_nested_parens(paren_string: str) -> List[int]:
    groups = paren_string.split()
    result = []
    for group in groups:
        depth = 0
        max_depth = 0
        for ch in group:
            if ch == '(':
                depth += 1
                if depth > max_depth:
                    max_depth = depth
            elif ch == ')':
                depth -= 1
        result.append(max_depth)
    return result