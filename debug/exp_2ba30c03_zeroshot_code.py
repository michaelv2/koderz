def make_palindrome(string: str) -> str:
    if not string:
        return string
    
    # Find the longest palindromic suffix
    for i in range(len(string)):
        if is_palindrome(string[i:]):
            # Append the reverse of the prefix before this suffix to the original string
            return string + string[:i][::-1]
    
    return string  # This line should never be reached because the loop will always find a palindromic suffix (at least the last character)