def compare(game, guess):
    return [abs(s - g) for s, g in zip(game, guess)]