def eat(number, need, remaining):
    to_eat = min(need, remaining)
    return [number + to_eat, remaining - to_eat]