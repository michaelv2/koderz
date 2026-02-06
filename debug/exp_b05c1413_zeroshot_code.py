def vowels_count(s):
    count = 0
    for char in s:
        # Check if the character is a vowel
        if char.lower() in 'aeiou':
            count += 1
        elif char.lower() == 'y' and len(s) > 1 and s[-2].lower() not in 'aeiou':
            # If it's 'y' at the end of a word, increment the count
            count += 1
    return count