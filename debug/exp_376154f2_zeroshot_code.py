def match_parens(lst):
    def is_balanced(s):
        balance = 0
        for char in s:
            if char == '(':
                balance += 1
            elif char == ')':
                balance -= 1
            if balance < 0:
                return False
        return balance == 0
    
    # Try both possible concatenations
    order1 = lst[0] + lst[1]
    order2 = lst[1] + lst[0]
    
    if is_balanced(order1) or is_balanced(order2):
        return 'Yes'
    else:
        return 'No'