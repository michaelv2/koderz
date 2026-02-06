def eat(number, need, remaining):
    to_eat = remaining if need > remaining else need
    return [number + to_eat, remaining - to_eat]