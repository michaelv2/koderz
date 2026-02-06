def correct_bracketing(brackets):
    count = 0
    for bracket in brackets:
        if bracket == "(":
            count += 1
        elif bracket == ")":
            count -= 1
        if count < 0:  # If there is a closing bracket before an opening one, it's not correct.
            return False
    return count == 0  # All brackets should be closed at the end.