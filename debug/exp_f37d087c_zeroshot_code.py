def reverse_delete(s, c):
    delete_set = set(c)
    filtered = ''.join(ch for ch in s if ch not in delete_set)
    return filtered, filtered == filtered[::-1]