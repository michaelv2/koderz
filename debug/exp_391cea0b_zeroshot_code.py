FIX = """
Add more test cases.

def vowels_count(s):
    """Return the number of vowels in s. Vowels are a, e, i, o, u (case-insensitive).
    If the last character is 'y' or 'Y', count it as a vowel as well.
    """
    if not isinstance(s, str):
        s = str(s)
    if not s:
        return 0

    vowels = set('aeiouAEIOU')
    count = sum(1 for ch in s[:-1] if ch in vowels)

    last = s[-1]
    if last in vowels or last in ('y', 'Y'):
        count += 1

    return count