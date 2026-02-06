import re

def fruit_distribution(s, n):
    # Extract numbers from the string using regex
    numbers = re.findall(r'\d+', s)
    apples = int(numbers[0])
    oranges = int(numbers[1])
    
    # Calculate mangoes: total - apples - oranges
    mangoes = n - apples - oranges
    
    return mangoes