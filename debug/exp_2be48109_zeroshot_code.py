def is_balanced(s):
    balance = 0
    for char in s:
        if char == '(':
            balance += 1
        else:
            balance -= 1
        if balance < 0:
            return False
    return balance == 0

def match_parens(lst):
    str1, str2 = lst
    if is_balanced(str1 + str2) or is_balanced(str2 + str1):
        return 'Yes'
    else:
        return 'No'