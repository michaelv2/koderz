def correct_bracketing(brackets: str) -> bool:
    balance = 0
    for ch in brackets:
        if ch == '<':
            balance += 1
        elif ch == '>':
            balance -= 1
            if balance < 0:
                return False
        else:
            continue
    return balance == 0