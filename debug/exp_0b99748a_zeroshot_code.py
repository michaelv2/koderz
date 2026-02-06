from typing import List

def string_xor(a: str, b: str) -> str:
    """ Input are two strings a and b consisting only of 1s and 0s.
    Perform binary XOR on these inputs and return result also as a string.
    """
    if len(a) != len(b):
        raise ValueError("Input strings must be of the same length")
    
    result = []
    for char_a, char_b in zip(a, b):
        # Convert characters to integers, perform XOR, and convert back to string
        xor_result = str(int(char_a) ^ int(char_b))
        result.append(xor_result)
    
    return ''.join(result)