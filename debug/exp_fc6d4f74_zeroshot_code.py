def eat(number, need, remaining):
    total_eaten = number + min(need, remaining)
    left = max(remaining - need, 0)
    return [total_eaten, left]