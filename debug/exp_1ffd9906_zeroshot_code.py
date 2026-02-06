def fruit_distribution(s, n):
    """
    Extract the number of apples and oranges from the string,
    then calculate mangoes as: total - apples - oranges
    """
    # Split the string and extract numbers
    parts = s.split()
    apples = int(parts[0])
    oranges = int(parts[3])
    
    # Calculate mangoes
    mangoes = n - apples - oranges
    return mangoes