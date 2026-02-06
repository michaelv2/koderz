def select_words(s, n):
    if not s:
        return []
    vowels = set("aeiouAEIOU")
    result = []
    for word in s.split():
        consonant_count = sum(1 for ch in word if ch.isalpha() and ch not in vowels)
        if consonant_count == n:
            result.append(word)
    return result