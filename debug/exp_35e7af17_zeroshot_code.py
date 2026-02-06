def make_palindrome(string: str) -> str:
    """ Find the shortest palindrome that begins with a supplied string.
    Algorithm idea is simple:
    - Find the longest postfix of supplied string that is a palindrome.
    - Append to the end of the string reverse of a string prefix that comes before the palindromic suffix.
    >>> make_palindrome('')
    ''
    >>> make_palindrome('cat')
    'catac'
    >>> make_palindrome('cata')
    'catac'
    """
    if not string:
        return string
    
    # Find the longest palindromic postfix
    for i in range(len(string)):
        # Check if substring from index i to end is palindrome
        if is_palindrome(string[i:]):
            # Take the prefix before this palindromic suffix
            prefix = string[:i]
            # Reverse the prefix and append to original string
            return string + prefix[::-1]
    
    # If no palindromic postfix found (shouldn't happen), return original string + reverse
    return string + string[:-1][::-1]