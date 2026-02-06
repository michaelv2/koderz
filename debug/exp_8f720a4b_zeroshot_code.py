def make_a_pile(n):
    pile = []
    stones = n
    for i in range(n):
        pile.append(stones)
        stones += 2
    return pile