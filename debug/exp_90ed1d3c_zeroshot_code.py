from typing import List

def below_zero(operations: List[int]) -> bool:
    bal = 0
    for op in operations:
        bal += op
        if bal < 0:
            return True
    return False