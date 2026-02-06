FIX = """
Add more test cases.
"""

def vowels_count(s):
    s = s.lower()
    vowels = {'a', 'e', 'i', 'o', 'u'}
    count = sum(1 for char in s if char in vowels)
    if s.endswith('y'):
        count += 1
    return count