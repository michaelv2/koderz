def file_name_check(file_name):
    """Create a function which takes a string representing a file's name, and returns
    'Yes' if the the file's name is valid, and returns 'No' otherwise.
    """
    # Must contain exactly one dot
    if file_name.count('.') != 1:
        return 'No'
    name, ext = file_name.split('.', 1)
    # Substring before dot should not be empty and starts with a latin letter
    if not name:
        return 'No'
    first = name[0]
    if not (first.isalpha() and first.isascii()):
        return 'No'
    # Extension must be one of the allowed
    if ext not in {'txt', 'exe', 'dll'}:
        return 'No'
    # No more than three digits in the whole file name
    digit_count = sum(1 for ch in file_name if ch.isdigit())
    if digit_count > 3:
        return 'No'
    return 'Yes'