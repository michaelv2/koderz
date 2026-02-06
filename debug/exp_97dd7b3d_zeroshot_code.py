def compare(game, guess):
    return [abs(score - g) for score, g in zip(game, guess)]