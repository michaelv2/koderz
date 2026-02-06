def fruit_distribution(s,n):
    # Split the string into words and convert them to integers
    fruits = [int(word) for word in s.split() if word.isdigit()]
    
    # Subtract the total number of apples and oranges from the total number of fruits
    mangoes = n - sum(fruits)
    
    return mangoes