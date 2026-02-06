def match_parens(lst):
    def is_good(s):
        bal = 0
        for ch in s:
            if ch == '(':
                bal += 1
            else:
                bal -= 1
            if bal < 0:
                return False
        return bal == 0

    a, b = lst[0], lst[1]
    if is_good(a + b) or is_good(b + a):
        return 'Yes'
    return 'No'