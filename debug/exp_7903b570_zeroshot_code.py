from typing import List

def string_xor(a: str, b: str) -> str:
    if len(a) != len(b):
        raise ValueError("Inputs must be of equal length.")
    return ''.join('0' if x == y else '1' for x, y in zip(a, b))