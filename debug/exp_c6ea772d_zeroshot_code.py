import re

def file_name_check(file_name):
    pattern = r"^[a-zA-Z][a-zA-Z0-9]{0,2}\.[txt|exe|dll]$"
    if re.match(pattern, file_name):
        return 'Yes'
    else:
        return 'No'