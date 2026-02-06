def eat(number, need, remaining):
    """
    Return [total eaten after meals, carrots left after meals].
    """
    if remaining >= need:
        return [number + need, remaining - need]
    else:
        return [number + remaining, 0]