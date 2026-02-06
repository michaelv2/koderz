def count_upper(s):
    count = 0
    uppercase_vowels = {'A', 'E', 'I', 'O', 'U'}
    for i in range(0, len(s), 2):
        if s[i] in uppercase_vowels:
            count += 1
    return count