def eat(number, need, remaining):
    if need <= remaining:
        # Enough carrots available
        total_eaten = number + need
        carrots_left = remaining - need
    else:
        # Not enough carrots, eat all remaining
        total_eaten = number + remaining
        carrots_left = 0
    
    return [total_eaten, carrots_left]