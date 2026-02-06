FIX = """
Add more test cases.
"""

def vowels_count(s):
    vowels = set("aeiouAEIOU")
    count = sum(1 for ch in s if ch in vowels)
    if s and (s[-1] == 'y' or s[-1] == 'Y'):
        count += 1
    return count