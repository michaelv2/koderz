def histogram(test):
    if not test:
        return {}
    
    # Split the input string into individual letters
    letters = test.split()
    
    # Count the occurrences of each letter
    from collections import Counter
    letter_counts = Counter(letters)
    
    # Find the maximum occurrence count
    max_count = max(letter_counts.values())
    
    # Collect all letters that have this maximum occurrence count
    result = {letter: count for letter, count in letter_counts.items() if count == max_count}
    
    return result