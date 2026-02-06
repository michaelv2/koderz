def file_name_check(file_name):
    """Create a function which takes a string representing a file's name, and returns
    'Yes' if the the file's name is valid, and returns 'No' otherwise.
    """
    if file_name.count('.') != 1:
        return 'No'
    name, ext = file_name.split('.', 1)
    if not name:
        return 'No'
    first = name[0]
    if not ('a' <= first <= 'z' or 'A' <= first <= 'Z'):
        return 'No'
    if ext not in ('txt', 'exe', 'dll'):
        return 'No'
    if sum(ch.isdigit() for ch in file_name) > 3:
        return 'No'
    return 'Yes'