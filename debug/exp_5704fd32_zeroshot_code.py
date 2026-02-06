def count_upper(s):
    # Initialize the counter to zero
    count = 0
    # Iterate over the string s with step 2 (even indices)
    for i in range(0, len(s), 2):
        # Check if the character is an uppercase vowel
        if s[i] in 'AEIOU':
            # If it is, increment the counter
            count += 1
    # Return the final count
    return count