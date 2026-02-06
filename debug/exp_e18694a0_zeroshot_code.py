def anti_shuffle(s):
    if not s:
        return s

    res = []
    i = 0
    n = len(s)

    while i < n:
        if s[i] == ' ':
            j = i
            while j < n and s[j] == ' ':
                j += 1
            res.append(s[i:j])
            i = j
        else:
            j = i
            while j < n and s[j] != ' ':
                j += 1
            word = s[i:j]
            res.append(''.join(sorted(word)))
            i = j

    return ''.join(res)