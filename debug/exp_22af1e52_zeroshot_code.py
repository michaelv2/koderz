def is_happy(s):
    if not isinstance(s, str):
        return False
    if len(s) < 3:
        return False
    for i in range(len(s) - 2):
        a, b, c = s[i], s[i + 1], s[i + 2]
        if a == b or a == c or b == c:
            return False
    return True