def make_a_pile(n):
    pile = []
    current_stones = n
    for i in range(n):
        pile.append(current_stones)
        if n % 2 == 0:
            current_stones += 1
        else:
            current_stones += 2
    return pile