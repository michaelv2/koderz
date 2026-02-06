def make_a_pile(n):
    pile = [n]
    current_stones = n
    
    for _ in range(1, n):
        if current_stones % 2 == 0:
            current_stones += 2
        else:
            current_stones += 2
        pile.append(current_stones)
    
    return pile