def eat(number, need, remaining):
    carrots_eaten_today = min(need, remaining)
    total_eaten = number + carrots_eaten_today
    carrots_left = remaining - carrots_eaten_today
    return [total_eaten, carrots_left]