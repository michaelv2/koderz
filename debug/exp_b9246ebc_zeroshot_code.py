def encode(message):
    vowels = 'aeiou'
    result = []
    
    for char in message:
        if char.isalpha():
            # Swap case
            swapped_char = char.lower() if char.isupper() else char.upper()
            
            # Check if it's a vowel (after swapping case)
            if swapped_char.lower() in vowels:
                # Find the letter 2 positions ahead
                if swapped_char.lower() == 'a':
                    replacement = 'c'
                elif swapped_char.lower() == 'e':
                    replacement = 'g'
                elif swapped_char.lower() == 'i':
                    replacement = 'k'
                elif swapped_char.lower() == 'o':
                    replacement = 'q'
                elif swapped_char.lower() == 'u':
                    replacement = 'w'
                
                # Preserve the original case
                if swapped_char.isupper():
                    result.append(replacement.upper())
                else:
                    result.append(replacement.lower())
            else:
                result.append(swapped_char)
        else:
            result.append(char)
    
    return ''.join(result)