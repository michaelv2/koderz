def fruit_distribution(s,n):
    # split the string into words and convert them to integers
    fruits = s.split()
    apples = int(fruits[0])
    oranges = int(fruits[2])
    
    # subtract the total number of apples and oranges from the total number of fruits
    mangoes = n - apples - oranges
    
    return mangoes