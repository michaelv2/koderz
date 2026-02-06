def count_upper(s):
    uppercase_vowels = set('AEIOU')
    count = 0
    
    for i in range(0, len(s), 2):  # iterate through even indices
        if s[i] in uppercase_vowels:
            count += 1
    
    return count