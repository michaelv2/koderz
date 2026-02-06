def correct_bracketing(brackets: str):
    balance = 0
    for bracket in brackets:
        if bracket == "<":
            balance += 1
        elif bracket == ">":
            balance -= 1
        # If balance goes negative, we have unmatched closing brackets
        if balance < 0:
            return False
    # All brackets matched if balance is exactly 0
    return balance == 0