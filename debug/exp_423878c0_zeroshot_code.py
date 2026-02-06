def reverse_delete(s, c):
    # Create a set of characters to delete for efficient lookup
    chars_to_delete = set(c)
    
    # Filter out characters that are in the deletion set
    result = ''.join(char for char in s if char not in chars_to_delete)
    
    # Check if the result is a palindrome
    is_palindrome = result == result[::-1]
    
    return (result, is_palindrome)