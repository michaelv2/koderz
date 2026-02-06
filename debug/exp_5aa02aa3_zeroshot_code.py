from typing import List

def parse_nested_parens(paren_string: str) -> List[int]:
    stack = []
    max_depths = []
    current_max = 0

    for char in paren_string:
        if char == '(':
            stack.append(char)
            current_max = max(current_max, len(stack))
        elif char == ')':
            stack.pop()
            if not stack:
                max_depths.append(current_max)
                current_max = 0
    return max_depths