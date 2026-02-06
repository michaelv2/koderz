def is_happy(s):
    if len(s) < 3:
        return False
    for i in range(len(s) - 2):
        if len({s[i], s[i + 1], s[i + 2]}) != 3:
            return False
    return True