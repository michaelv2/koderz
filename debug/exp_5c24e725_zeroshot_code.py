import math
from typing import List

def poly(xs: List[float], x: float) -> float:
    return sum([coeff * math.pow(x, i) for i, coeff in enumerate(xs)])

def find_zero(xs: List[float]) -> float:
    n = len(xs) // 2
    a = xs[-1]
    b = 0
    for i in range(n-1):
        b += (i+1)*xs[-i-2]*(-1)**i
    return b / a