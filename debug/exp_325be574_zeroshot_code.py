def file_name_check(file_name):
    # Check if there is exactly one dot in the file name
    parts = file_name.split('.')
    if len(parts) != 2:
        return 'No'
    
    # Extract the name and extension
    name, extension = parts
    
    # Check if the name starts with a letter and is not empty
    if not name or not name[0].isalpha():
        return 'No'
    
    # Count the number of digits in the file name
    digit_count = sum(c.isdigit() for c in file_name)
    if digit_count > 3:
        return 'No'
    
    # Check if the extension is one of the allowed types
    if extension not in ['txt', 'exe', 'dll']:
        return 'No'
    
    return 'Yes'