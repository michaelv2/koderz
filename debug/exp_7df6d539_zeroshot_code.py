def match_parens(lst):
    def balanced(s: str) -> bool:
        bal = 0
        for ch in s:
            if ch == '(':
                bal += 1
            elif ch == ')':
                bal -= 1
            else:
                # Per problem statement, input consists only of '(' and ')'
                continue
            if bal < 0:
                return False
        return bal == 0

    if len(lst) != 2:
        s = ''.join(lst)
        return 'Yes' if balanced(s) else 'No'

    for i in range(2):
        if balanced(lst[i] + lst[1 - i]):
            return 'Yes'
    return 'No'