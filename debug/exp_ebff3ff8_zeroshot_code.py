def reverse_delete(s, c):
    """Given strings s and c, remove all characters in s that appear in c.
    Then return a tuple of (resulting_string, is_palindrome).
    """
    del_chars = set(c)
    filtered = ''.join(ch for ch in s if ch not in del_chars)
    return filtered, (filtered == filtered[::-1])