from typing import List

def string_xor(a: str, b: str) -> str:
    return ''.join('1' if bit_a != bit_b else '0' for bit_a, bit_b in zip(a, b))