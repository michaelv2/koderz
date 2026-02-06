def anti_shuffle(s):
    res = []
    i = 0
    n = len(s)
    while i < n:
        if s[i] == ' ':
            res.append(' ')
            i += 1
        else:
            j = i
            while j < n and s[j] != ' ':
                j += 1
            word = s[i:j]
            res.append(''.join(sorted(word)))
            i = j
    return ''.join(res)