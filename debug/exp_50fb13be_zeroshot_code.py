def separate_paren_groups(paren_string: str) -> List[str]:
    result = []
    balance = 0
    start_index = 0
    
    for i, char in enumerate(paren_string):
        if char == ' ':
            continue
        if char == '(':
            if balance == 0:
                start_index = i
            balance += 1
        elif char == ')':
            balance -= 1
            if balance == 0:
                result.append(paren_string[start_index:i+1])
    
    return result