def below_threshold(l: list, t: int) -> bool:
    for num in l:
        if num >= t:
            return False
    return True