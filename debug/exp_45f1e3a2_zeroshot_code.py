def file_name_check(file_name):
    # Check if there's exactly one dot
    if file_name.count('.') != 1:
        return 'No'
    
    # Split by dot
    parts = file_name.split('.')
    name_part = parts[0]
    extension = parts[1]
    
    # Check if name part is not empty and starts with a letter
    if not name_part or not name_part[0].isalpha():
        return 'No'
    
    # Check if extension is one of the valid ones
    if extension not in ['txt', 'exe', 'dll']:
        return 'No'
    
    # Count digits in the entire filename
    digit_count = sum(1 for char in file_name if char.isdigit())
    if digit_count > 3:
        return 'No'
    
    return 'Yes'