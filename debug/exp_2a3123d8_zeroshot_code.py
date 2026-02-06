def anti_shuffle(s):
    words = s.split(' ')
    sorted_words = [''.join(sorted(word)) for word in words]
    
    # Replace each word with its sorted version
    for i, word in enumerate(words):
        s = s.replace(word, sorted_words[i])
        
    return s