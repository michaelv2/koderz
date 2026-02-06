def compare(game, guess):
    return [0 if g == gu else abs(g - gu) for g, gu in zip(game, guess)]