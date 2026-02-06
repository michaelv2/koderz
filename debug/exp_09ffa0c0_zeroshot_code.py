def make_palindrome(string: str) -> str:
    """ Find the shortest palindrome that begins with a supplied string. """
    if not string:
        return ''
    for i in range(len(string)):
        if string[i:] == string[i:][::-1]:
            return string + string[:i][::-1]
    # fallback (shouldn't be reached because last char is always a palindrome)
    return string + string[:-1][::-1]