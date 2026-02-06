def make_palindrome(string: str) -> str:
    """Find the shortest palindrome that begins with the supplied string."""
    n = len(string)
    for i in range(n):
        if string[i:] == string[i:][::-1]:
            return string + string[:i][::-1]
    return string