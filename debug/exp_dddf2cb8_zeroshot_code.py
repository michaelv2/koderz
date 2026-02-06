def select_words(s, n):
    """Given a string s and a natural number n, return list of words that contain exactly n consonants."""
    vowels = set('aeiou')
    result = []
    for word in s.split():
        count = 0
        for ch in word.lower():
            if ch.isalpha() and ch not in vowels:
                count += 1
        if count == n:
            result.append(word)
    return result