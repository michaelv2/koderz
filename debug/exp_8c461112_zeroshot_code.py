def fix_spaces(text):
    """
    Replace spaces with underscores, but if there is a run of more than two consecutive
    spaces, replace the entire run with a single dash.
    Example:
    fix_spaces(" Example   3") -> "_Example-3"
    """
    if not isinstance(text, str):
        text = str(text)
    res = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] != ' ':
            res.append(text[i])
            i += 1
        else:
            j = i
            while j < n and text[j] == ' ':
                j += 1
            run = j - i
            if run <= 2:
                res.append('_' * run)
            else:
                res.append('-')
            i = j
    return ''.join(res)