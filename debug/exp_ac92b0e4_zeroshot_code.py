def select_words(s, n):
    # Define a set of vowels for easy lookup
    vowels = {'a', 'e', 'i', 'o', 'u'}

    # Split the string into words
    words = s.split()

    # Initialize an empty list to store the result
    result = []

    # Iterate over each word in the list of words
    for word in words:
        # Count the number of consonants in the current word
        consonant_count = sum(1 for char in word if char.lower() not in vowels)

        # If the count matches 'n', add the word to the result list
        if consonant_count == n:
            result.append(word)

    return result