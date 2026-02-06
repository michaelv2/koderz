def select_words(s, n):
    if not s:
        return []
    vowels = set('aeiou')
    result = []
    for word in s.split():
        consonants = sum(1 for ch in word if ch.lower() not in vowels)
        if consonants == n:
            result.append(word)
    return result