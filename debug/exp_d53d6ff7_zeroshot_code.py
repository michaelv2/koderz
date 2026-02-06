def get_closest_vowel(word):
    vowels = "aeiouAEIOU"
    
    # Start from right side, but not including the last character
    # We need at least one character to the right (consonant requirement)
    for i in range(len(word) - 2, 0, -1):  # range goes from len-2 down to 1 (not 0, since we need consonant on left)
        if word[i] in vowels:
            # Check if there's a consonant on the right and left
            if word[i - 1] not in vowels and word[i + 1] not in vowels:
                return word[i]
    
    return ""