from typing import List

def string_xor(a: str, b: str) -> str:
    """ Input are two strings a and b consisting only of 1s and 0s.
    Perform binary XOR on these inputs and return result also as a string.
    """
    if len(a) != len(b):
        raise ValueError("Input strings must be of the same length")
    
    result = []
    for char_a, char_b in zip(a, b):
        # XOR operation: 1 if characters are different, 0 if they are the same
        xor_result = '1' if char_a != char_b else '0'
        result.append(xor_result)
    
    return ''.join(result)