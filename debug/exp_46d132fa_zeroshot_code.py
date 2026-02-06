def get_closest_vowel(word):
    if len(word) < 3:
        return ""
    
    vowels = set('aeiouAEIOU')
    
    # Iterate from right to left, but skip the last character (end)
    for i in range(len(word) - 2, 0, -1):
        # Check if current character is a vowel
        if word[i] in vowels:
            # Check if it's between two consonants
            if word[i-1] not in vowels and word[i+1] not in vowels:
                return word[i]
    
    return ""