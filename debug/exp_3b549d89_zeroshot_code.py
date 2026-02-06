def cycpattern_check(a, b):
    def rotate(s, i):
        return s[i:] + s[:i]

    for i in range(len(b)):
        if rotate(b, i) in a:
            return True
    return False