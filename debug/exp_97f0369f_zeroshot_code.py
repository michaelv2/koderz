from typing import List

def parse_nested_parens(paren_string: str) -> List[int]:
    if not paren_string:
        return []
    
    def max_nesting(s: str) -> int:
        depth = 0
        max_depth = 0
        for ch in s:
            if ch == '(':
                depth += 1
                if depth > max_depth:
                    max_depth = depth
            elif ch == ')':
                depth = max(depth - 1, 0)
        return max_depth

    return [max_nesting(token) for token in paren_string.split()]