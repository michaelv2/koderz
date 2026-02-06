def correct_bracketing(brackets):
    open_count = 0
    for bracket in brackets:
        if bracket == '<':
            open_count += 1
        elif bracket == '>':
            if open_count == 0:
                return False
            else:
                open_count -= 1
    return open_count == 0