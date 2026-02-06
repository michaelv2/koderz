def match_parens(lst):
    def is_balanced(s):
        balance = 0
        for char in s:
            if char == '(':
                balance += 1
            else:  # char == ')'
                balance -= 1
            if balance < 0:
                return False
        return balance == 0
    
    # Try both concatenation orders
    if is_balanced(lst[0] + lst[1]) or is_balanced(lst[1] + lst[0]):
        return 'Yes'
    else:
        return 'No'