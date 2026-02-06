def fix_spaces(text):
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
            run_len = j - i
            if run_len > 2:
                res.append('-')
            else:
                res.append('_' * run_len)
            i = j
    return ''.join(res)