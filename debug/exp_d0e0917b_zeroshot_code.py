from typing import List

def separate_paren_groups(paren_string: str) -> List[str]:
    paren_string = paren_string.replace(" ", "")  # Remove spaces from the string
    groups = []
    group = ""
    open_count = 0
    
    for char in paren_string:
        if char == '(':
            open_count += 1
        elif char == ')':
            open_count -= 1
            
        group += char  # Add the character to the current group
        
        if open_count == 0:  # If we have closed all opened parentheses, we found a group
            groups.append(group)
            group = ""  # Reset for next group
    
    return groups