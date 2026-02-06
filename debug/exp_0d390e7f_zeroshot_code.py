import re

def fruit_distribution(s, n):
    a_match = re.search(r'(-?\d+)\s*apples', s, flags=re.IGNORECASE)
    o_match = re.search(r'(-?\d+)\s*oranges', s, flags=re.IGNORECASE)
    apples = int(a_match.group(1)) if a_match else 0
    oranges = int(o_match.group(1)) if o_match else 0
    return int(n) - apples - oranges