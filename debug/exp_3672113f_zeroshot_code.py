def fix_spaces(text):
    """
    Given a string text, replace all spaces in it with underscores, 
    and if a string has more than 2 consecutive spaces, 
    then replace all consecutive spaces with -
    """
    res = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == ' ':
            j = i
            while j < n and text[j] == ' ':
                j += 1
            count = j - i
            if count >= 3:
                res.append('-')
            else:
                res.append('_' * count)
            i = j
        else:
            res.append(text[i])
            i += 1
    return ''.join(res)