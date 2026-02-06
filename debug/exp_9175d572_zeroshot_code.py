def match_parens(lst):
    def analyze(s):
        balance = 0
        min_pref = 0
        for ch in s:
            if ch == '(':
                balance += 1
            else:
                balance -= 1
            min_pref = min(min_pref, balance)
        return balance, min_pref

    s1, s2 = lst[0], lst[1]
    t1, m1 = analyze(s1)
    t2, m2 = analyze(s2)

    # Check order: s1 + s2
    if m1 >= 0 and (t1 + m2) >= 0 and (t1 + t2) == 0:
        return "Yes"
    # Check order: s2 + s1
    if m2 >= 0 and (t2 + m1) >= 0 and (t1 + t2) == 0:
        return "Yes"
    return "No"