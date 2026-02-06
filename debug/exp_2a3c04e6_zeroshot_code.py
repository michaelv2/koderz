def fruit_distribution(s, n):
    # Extract numbers of apples and oranges from the string
    apple_str, orange_str = s.split('apples and')[0].strip(), s.split('oranges')[0].strip()

    # Convert strings to integers
    apples = int(apple_str)
    oranges = int(orange_str)

    # Calculate number of mangoes
    mangoes = n - apples - oranges

    return mangoes