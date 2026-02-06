from typing import List

def parse_nested_parens(paren_string: str) -> List[int]:
    # Split the input string into individual groups
    groups = paren_string.split()
    
    # Initialize a list to store the maximum depth for each group
    max_depths = []
    
    # Process each group separately
    for group in groups:
        current_depth = 0
        max_depth = 0
        
        # Iterate through each character in the group
        for char in group:
            if char == '(':
                current_depth += 1
                # Update max depth if current depth is greater
                if current_depth > max_depth:
                    max_depth = current_depth
            elif char == ')':
                current_depth -= 1
        
        # Append the maximum depth of this group to the list
        max_depths.append(max_depth)
    
    return max_depths