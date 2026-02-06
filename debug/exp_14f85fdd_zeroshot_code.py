import re

def file_name_check(file_name):
    # Regular expression to match the file name criteria
    pattern = r'^[a-zA-Z][^\d]*\d{0,3}[^\d]*\.(txt|exe|dll)$'
    return 'Yes' if re.match(pattern, file_name) else 'No'