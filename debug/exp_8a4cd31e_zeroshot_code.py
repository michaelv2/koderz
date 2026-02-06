def correct_bracketing(brackets: str) -> bool:
    balance = 0
    for char in brackets:
        if char == '(':
            balance += 1
        elif char == ')':
            balance -= 1
        # If balance is negative, there are more closing brackets than opening ones
        if balance < 0:
            return False
    # If balance is zero, all opening brackets have been matched
    return balance == 0