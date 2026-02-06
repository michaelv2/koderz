def correct_bracketing(brackets: str):
    """ brackets is a string of "<" and ">".
    return True if every opening bracket has a corresponding closing bracket.

    >>> correct_bracketing("<")
    False
    >>> correct_bracketing("<>")
    True
    >>> correct_bracketing("<<><>>")
    True
    >>> correct_bracketing("><<>")
    False
    """
    count = 0
    for char in brackets:
        if char == "<":
            count += 1
        elif char == ">":
            count -= 1
        
        # If count goes negative, we have a closing bracket without opening
        if count < 0:
            return False
    
    # At the end, count must be 0 for all brackets to be matched
    return count == 0