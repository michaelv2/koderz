def compare(game, guess):
    result = []
    for i in range(len(game)):
        difference = abs(game[i] - guess[i])
        result.append(difference)
    return result