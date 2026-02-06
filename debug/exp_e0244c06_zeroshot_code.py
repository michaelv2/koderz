def fix_spaces(text):
    """
    Replace spaces with underscores, but any run of 3 or more spaces is replaced by a single dash.
    """
    if not text:
        return text

    result = []
    i = 0
    n = len(text)

    while i < n:
        if text[i] == ' ':
            j = i
            while j < n and text[j] == ' ':
                j += 1
            run_len = j - i
            if run_len >= 3:
                result.append('-')
            else:
                result.append('_' * run_len)
            i = j
        else:
            result.append(text[i])
            i += 1

    return ''.join(result)