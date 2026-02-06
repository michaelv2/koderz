def correct_bracketing(brackets: str) -> bool:
    unmatched = 0
    for b in brackets:
        if b == '<':
            unmatched += 1
        elif b == '>':
            if unmatched == 0:
                return False
            else:
                unmatched -= 1
    return unmatched == 0