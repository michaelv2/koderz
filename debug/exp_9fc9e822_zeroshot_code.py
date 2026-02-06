from typing import List

def parse_nested_parens(paren_string: str) -> List[int]:
    def max_depth(group):
        current_depth = 0
        max_nesting = 0
        for char in group:
            if char == '(':
                current_depth += 1
                max_nesting = max(max_nesting, current_depth)
            elif char == ')':
                current_depth -= 1
        return max_nesting

    return [max_depth(group) for group in paren_string.split()]