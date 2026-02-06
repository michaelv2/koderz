def select_words(s, n):
    if not s:
        return []
    
    vowels = set('aeiouAEIOU')
    result = []
    
    words = s.split()
    
    for word in words:
        consonant_count = 0
        for char in word:
            if char.isalpha() and char not in vowels:
                consonant_count += 1
        
        if consonant_count == n:
            result.append(word)
    
    return result