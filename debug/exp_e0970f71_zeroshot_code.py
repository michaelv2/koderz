def solve(s):
    if any(ch.isalpha() for ch in s):
        return s.swapcase()
    else:
        return s[::-1]