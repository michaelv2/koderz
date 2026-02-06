def match_parens(lst):
    a, b = lst

    def good(s: str) -> bool:
        bal = 0
        for ch in s:
            if ch == '(':
                bal += 1
            else:
                bal -= 1
            if bal < 0:
                return False
        return bal == 0

    return 'Yes' if good(a + b) or good(b + a) else 'No'