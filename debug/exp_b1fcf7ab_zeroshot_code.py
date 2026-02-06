def match_parens(lst):
    def good(s):
        cnt = 0
        for ch in s:
            if ch == '(':
                cnt += 1
            else:
                cnt -= 1
            if cnt < 0:
                return False
        return cnt == 0
    a, b = lst
    return 'Yes' if good(a + b) or good(b + a) else 'No'