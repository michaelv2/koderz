def anti_shuffle(s):
    words = s.split(' ')
    sorted_words = []
    
    for word in words:
        # Sort characters in the word by ASCII value
        sorted_word = ''.join(sorted(word))
        sorted_words.append(sorted_word)
    
    # Join the sorted words back with spaces
    return ' '.join(sorted_words)