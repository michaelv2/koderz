def eat(number, need, remaining):
    total_needed = number + need
    if total_needed > remaining:
        return [number + remaining, 0]
    else:
        return [total_needed, remaining - total_needed]