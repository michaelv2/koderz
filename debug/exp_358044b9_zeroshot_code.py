def make_palindrome(string: str) -> str:
    """Find the shortest palindrome that begins with the given string."""
    n = len(string)
    for k in range(n):
        if is_palindrome(string[k:]):
            return string + string[:k][::-1]
    return string