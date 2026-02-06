def is_nested(string):
    open_brackets = 0
    for char in string:
        if char == '[':
            open_brackets += 1
        elif char == ']':
            open_brackets -= 1
        # If there are more than one unmatched opening brackets, we have a nested structure
        if open_brackets > 1:
            return True
    return False