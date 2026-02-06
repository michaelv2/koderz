def reverse_delete(s, c):
    removed = ''.join(ch for ch in s if ch not in set(c))
    return (removed, removed == removed[::-1])