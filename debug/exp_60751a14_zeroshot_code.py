def fix_spaces(text):
    res = []
    run = 0
    for ch in text:
        if ch == ' ':
            run += 1
        else:
            if run:
                res.append('-' if run > 2 else '_' * run)
                run = 0
            res.append(ch)
    if run:
        res.append('-' if run > 2 else '_' * run)
    return ''.join(res)