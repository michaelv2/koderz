from typing import List

def separate_paren_groups(paren_string: str) -> List[str]:
    groups = []
    current_group = ""
    balance = 0
    
    for char in paren_string:
        if char == ' ':
            continue
        if char == '(':
            balance += 1
        elif char == ')':
            balance -= 1
        
        current_group += char
        
        if balance == 0:
            groups.append(current_group)
            current_group = ""
    
    return groups