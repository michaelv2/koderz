from typing import List

def string_xor(a: str, b: str) -> str:
    """Input are two strings a and b consisting only of 1s and 0s.
    Perform binary XOR on these inputs and return result also as a string.
    """
    n = max(len(a), len(b))
    out_bits = []
    for i in range(n):
        bit_a = a[-1 - i] if i < len(a) else '0'
        bit_b = b[-1 - i] if i < len(b) else '0'
        out_bits.append('1' if bit_a != bit_b else '0')
    return ''.join(reversed(out_bits))