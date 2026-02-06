def histogram(test):
    # Split the string into words and count each word's occurrence
    counts = dict()
    for letter in test.split():
        counts[letter] = counts.get(letter, 0) + 1
    
    # Find the maximum count
    max_count = max(counts.values()) if counts else 0
    
    # Filter out letters with count equal to max_count
    result = {k: v for k, v in counts.items() if v == max_count}
    
    return result