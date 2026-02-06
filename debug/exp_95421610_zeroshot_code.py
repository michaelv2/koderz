from typing import List

def parse_nested_parens(paren_string: str) -> List[int]:
    """
    Given a string consisting of groups of parentheses separated by spaces,
    return a list of the maximum nesting depth for each group.
    """
    results: List[int] = []
    for group in paren_string.split():
        depth = 0
        max_depth = 0
        for ch in group:
            if ch == '(':
                depth += 1
                if depth > max_depth:
                    max_depth = depth
            elif ch == ')':
                depth -= 1
        results.append(max_depth)
    return results