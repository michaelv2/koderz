def is_nested(string):
    stack = []
    for bracket in string:
        if bracket == '[':
            stack.append(bracket)
        else:
            if not stack or stack[-1] != '[':
                return True
            stack.pop()
    return False