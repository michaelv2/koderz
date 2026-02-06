def correct_bracketing(brackets: str) -> bool:
    open_count = 0
    close_count = 0
    for b in brackets:
        if b == '(':
            open_count += 1
        elif b == ')':
            close_count += 1
        if close_count > open_count:
            return False
    return open_count == close_count