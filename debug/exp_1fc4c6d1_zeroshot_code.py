def file_name_check(file_name):
    """Return 'Yes' if file_name is valid according to:
    - At most three digits in the entire name
    - Exactly one dot '.'
    - Non-empty prefix before dot that starts with a Latin letter
    - Suffix after dot must be one of 'txt', 'exe', 'dll'
    Otherwise return 'No'.
    """
    # Must contain exactly one dot
    if file_name.count('.') != 1:
        return 'No'
    
    prefix, suffix = file_name.split('.', 1)
    
    # Prefix must be non-empty and start with a letter
    if not prefix:
        return 'No'
    if not prefix[0].isalpha():
        return 'No'
    
    # Suffix must be one of the allowed extensions exactly as given (case-sensitive)
    if suffix not in ('txt', 'exe', 'dll'):
        return 'No'
    
    # There should not be more than three digits in the entire file_name
    digits = sum(ch.isdigit() for ch in file_name)
    if digits > 3:
        return 'No'
    
    return 'Yes'