def make_palindrome(string: str) -> str:
    """ Find the shortest palindrome that begins with a supplied string. """
    n = len(string)
    for i in range(n, -1, -1):
        if is_palindrome(string[:i]):
            prefix_to_reverse = string[i:]
            return string + prefix_to_reverse[::-1]
    return string