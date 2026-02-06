FIX = """
Add more test cases.
"""

def vowels_count(s):
    s = s.lower()
    vowels = set("aeiou")
    count = 0
    n = len(s)
    for i, ch in enumerate(s):
        if ch in vowels or (ch == "y" and i == n - 1):
            count += 1
    return count