def reverse_delete(s, c):
    filtered = [ch for ch in s if ch not in c]
    res = ''.join(filtered)
    return res, res == res[::-1]