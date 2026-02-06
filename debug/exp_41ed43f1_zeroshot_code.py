def histogram(test):
    if not test:
        return {}
    
    # Split the string into letters
    letters = test.split()
    
    # Count frequency of each letter
    count = {}
    for letter in letters:
        count[letter] = count.get(letter, 0) + 1
    
    # Find the maximum frequency
    max_count = max(count.values())
    
    # Return all letters with maximum frequency
    return {letter: count for letter, count in count.items() if count == max_count}