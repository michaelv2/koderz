def file_name_check(file_name):
    # Check if there's exactly one dot
    if file_name.count('.') != 1:
        return 'No'
    
    # Split into name and extension
    name_part, extension = file_name.split('.')
    
    # Check if extension is valid
    if extension not in ['txt', 'exe', 'dll']:
        return 'No'
    
    # Check if name part is not empty
    if not name_part:
        return 'No'
    
    # Check if name part starts with a letter
    if not name_part[0].isalpha():
        return 'No'
    
    # Count digits in the entire filename
    digit_count = sum(1 for char in file_name if char.isdigit())
    if digit_count > 3:
        return 'No'
    
    return 'Yes'