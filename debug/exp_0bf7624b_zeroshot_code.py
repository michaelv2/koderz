from typing import List

def string_xor(a: str, b: str) -> str:
    """Input are two strings a and b consisting only of '1's and '0's.
    Perform binary XOR on these inputs and return the result as a string.

    The two inputs must be of the same length.
    """
    if len(a) != len(b):
        raise ValueError("Inputs must have the same length.")
    return ''.join('1' if x != y else '0' for x, y in zip(a, b))