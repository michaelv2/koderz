def split_words(txt):
    # Check for whitespace
    if ' ' in txt:
        return txt.split(' ')
    # If no whitespace, check for commas
    elif ',' in txt:
        return txt.split(',')
    # If no whitespace or comma, count lowercase letters with odd order
    else:
        return sum([1 for c in txt if c.islower() and (ord(c) - ord('a')) % 2 == 1])