def histogram(test):
    if not test:
        return {}
    
    letters = test.split()
    
    # Count occurrences of each letter
    counts = {}
    for letter in letters:
        counts[letter] = counts.get(letter, 0) + 1
    
    # Find the maximum count
    max_count = max(counts.values())
    
    # Return all letters with the maximum count
    result = {letter: count for letter, count in counts.items() if count == max_count}
    
    return result