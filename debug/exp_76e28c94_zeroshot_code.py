FIX = """
Add more test cases.

def vowels_count(s):
    """Return the number of vowels in the string s.
    Vowels: a, e, i, o, u (case-insensitive). Additionally, 'y' counts
    as a vowel only if it is the final character of the string.
    """
    if not s:
        return 0
    lower = s.lower()
    base_vowels = set("aeiou")
    count = sum(1 for ch in lower if ch in base_vowels)
    if lower[-1] == "y":
        count += 1
    return count