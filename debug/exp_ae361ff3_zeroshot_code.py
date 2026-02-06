from typing import List

def below_zero(operations: List[int]) -> bool:
    """You're given a list of deposit and withdrawal operations on a bank account that starts with
    zero balance. Return True if at any point the balance falls below zero, otherwise False."""
    balance = 0
    for op in operations:
        balance += op
        if balance < 0:
            return True
    return False