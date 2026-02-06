def solve(s):
    if any(c.isalpha() for c in s):
        return s.swapcase()
    else:
        return s[::-1]