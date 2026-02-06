import re

def fix_spaces(text):
    # Replace multiple spaces with '-'
    text = re.sub(' {2,}', '-', text)
    # Replace single spaces with '_'
    text = text.replace(' ', '_')
    return text