def fix_spaces(text):
    result = []
    space_count = 0
    
    for char in text:
        if char == ' ':
            space_count += 1
        else:
            if space_count == 1:
                result.append('_')
            elif space_count == 2:
                result.append('__')
            elif space_count > 2:
                result.append('-')
            space_count = 0
            result.append(char)
    
    # Handle trailing spaces
    if space_count == 1:
        result.append('_')
    elif space_count == 2:
        result.append('__')
    elif space_count > 2:
        result.append('-')
    
    return ''.join(result)