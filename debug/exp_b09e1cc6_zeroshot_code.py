def correct_bracketing(brackets):
    count = 0
    for bracket in brackets:
        if bracket == "<":
            count += 1
        elif bracket == ">":
            count -= 1
        if count < 0:  # If there is a closing bracket without an opening one, return False immediately.
            return False
    return count == 0  # If all brackets are paired up correctly, the count should be zero.