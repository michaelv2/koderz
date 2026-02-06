def select_words(s, n):
    vowels = set('aeiou')
    result = []
    if not s:
        return result
    for word in s.split():
        consonant_count = sum(1 for ch in word if ch.isalpha() and ch.lower() not in vowels)
        if consonant_count == n:
            result.append(word)
    return result