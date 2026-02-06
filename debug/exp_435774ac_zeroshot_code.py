from typing import List

def parse_nested_parens(paren_string: str) -> List[int]:
    """Compute the maximum nesting depth for each space-separated group of parentheses.
    
    Each group consists of parentheses characters '(' and ')'. The function returns
    a list of integers representing the deepest nesting level found in each group.
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