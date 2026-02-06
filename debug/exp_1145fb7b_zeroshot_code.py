FIX = """
Add more test cases.
"""

def vowels_count(s):
    s = s.lower()
    count = 0
    for i in range(len(s)):
        if s[i] in 'aeiou':
            count += 1
        elif s[i] == 'y' and i == len(s) - 1:
            count += 1
    return count