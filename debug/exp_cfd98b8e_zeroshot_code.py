from typing import List

def parse_nested_parens(paren_string: str) -> List[int]:
    """ Input to this function is a string represented multiple groups for nested parentheses separated by spaces.
    For each of the group, output the deepest level of nesting of parentheses.
    """
    if not paren_string:
        return []
    groups = paren_string.split()
    result: List[int] = []
    for g in groups:
        max_depth = 0
        depth = 0
        for ch in g:
            if ch == '(':
                depth += 1
                if depth > max_depth:
                    max_depth = depth
            elif ch == ')':
                depth -= 1
        result.append(max_depth)
    return result