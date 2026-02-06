import re

def fix_spaces(text):
    # Replace all spaces with underscores
    text = text.replace(' ', '_')
    
    # If there are more than 2 consecutive underscores, replace them with -
    text = re.sub(r'_{3,}', '-', text)
    
    return text