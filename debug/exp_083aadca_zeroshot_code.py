def file_name_check(file_name):
    digits = sum(ch.isdigit() for ch in file_name)
    if digits > 3:
        return 'No'
    if file_name.count('.') != 1:
        return 'No'
    name, ext = file_name.split('.', 1)
    if not name:
        return 'No'
    first = name[0]
    if not (('a' <= first <= 'z') or ('A' <= first <= 'Z')):
        return 'No'
    if ext not in ('txt', 'exe', 'dll'):
        return 'No'
    return 'Yes'