def match_parens(lst):
    def calculate_balance(s):
        balance = 0
        min_balance = 0
        for char in s:
            if char == '(':
                balance += 1
            else:
                balance -= 1
            min_balance = min(min_balance, balance)
        return balance, min_balance

    s1, s2 = lst
    balance1, min_balance1 = calculate_balance(s1)
    balance2, min_balance2 = calculate_balance(s2)

    # Check s1 + s2
    if balance1 + min_balance2 >= 0 and balance1 + balance2 == 0:
        return 'Yes'
    
    # Check s2 + s1
    if balance2 + min_balance1 >= 0 and balance2 + balance1 == 0:
        return 'Yes'
    
    return 'No'