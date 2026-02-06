def correct_bracketing(brackets: str) -> bool:
    balance = 0
    for char in brackets:
        if char == '<':
            balance += 1
        elif char == '>':
            balance -= 1
        # If balance is negative, there are more '>' than '<' at some point
        if balance < 0:
            return False
    # If balance is not zero, there are unmatched '<'
    return balance == 0