def is_nested(string):
    n = len(string)
    for i in range(n):
        if string[i] != '[':
            continue
        for j in range(i+1, n):
            if string[j] != '[':
                continue
            for k in range(j+1, n):
                if string[k] != ']':
                    continue
                for l in range(k+1, n):
                    if string[l] == ']':
                        return True
    return False