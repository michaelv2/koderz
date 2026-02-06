def get_closest_vowel(word):
    vowels = set("aeiouAEIOU")
    n = len(word)
    if n < 3:
        return ""
    # scan from right to left for positions that are not first or last
    for i in range(n - 2, 0, -1):
        ch = word[i]
        if ch in vowels:
            if word[i - 1] not in vowels and word[i + 1] not in vowels:
                return ch
    return ""