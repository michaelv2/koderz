def fix_spaces(text):
    result = []
    i = 0
    while i < len(text):
        if text[i] == ' ':
            # Count consecutive spaces
            space_count = 0
            while i < len(text) and text[i] == ' ':
                space_count += 1
                i += 1
            
            # Replace based on count
            if space_count >= 3:
                result.append('-')
            else:
                result.append('_' * space_count)
        else:
            result.append(text[i])
            i += 1
    
    return ''.join(result)