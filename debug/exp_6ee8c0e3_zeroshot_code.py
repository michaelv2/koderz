def select_words(s, n):
    """Given a string s and a natural number n, return a list of all words from s that contain exactly n consonants."""
    if not s:
        return []
    vowels = set('aeiouAEIOU')
    result = []
    for word in s.split():
        consonant_count = sum(1 for ch in word if ch not in vowels)
        if consonant_count == n:
            result.append(word)
    return result