def reverse_delete(s, c):
    # Create a set of characters to delete for faster lookup
    chars_to_delete = set(c)
    
    # Construct the result string by excluding characters in chars_to_delete
    result_string = ''.join(char for char in s if char not in chars_to_delete)
    
    # Check if the result string is a palindrome
    is_palindrome = result_string == result_string[::-1]
    
    # Return the result as a tuple
    return (result_string, is_palindrome)