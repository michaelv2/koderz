import re

def fix_spaces(text):
    # First, replace sequences of 3 or more spaces with a single dash
    text = re.sub(r' {3,}', '-', text)
    # Then, replace remaining single spaces with underscores
    text = text.replace(' ', '_')
    return text