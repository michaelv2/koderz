def correct_bracketing(brackets: str):
    count = 0
    for ch in brackets:
        if ch == "<":
            count += 1
        else:  # assume ">"
            count -= 1
            if count < 0:
                return False
    return count == 0