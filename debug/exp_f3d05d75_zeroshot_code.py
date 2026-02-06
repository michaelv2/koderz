from typing import List

def below_zero(operations: List[int]) -> bool:
    balance = 0
    for amount in operations:
        balance += amount
        if balance < 0:
            return True
    return False