from typing import List

def string_xor(a: str, b: str) -> str:
    """Input are two strings a and b consisting only of 1s and 0s.
    Perform binary XOR on these inputs and return result also as a string.
    """
    if len(a) != len(b):
        raise ValueError("Input strings must be of equal length.")
    return ''.join('0' if x == y else '1' for x, y in zip(a, b))