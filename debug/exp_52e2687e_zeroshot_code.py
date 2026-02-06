def vowels_count(s):
    if not s:
        return 0
    
    vowels = set('aeiou')
    count = 0
    s_lower = s.lower()
    
    for i, char in enumerate(s_lower):
        if char in vowels:
            count += 1
        elif char == 'y' and i == len(s_lower) - 1:
            count += 1
    
    return count