def find_max(words):
    if not words:
        return ""
    
    max_word = words[0]
    max_unique = len(set(words[0]))
    
    for word in words[1:]:
        unique_count = len(set(word))
        if unique_count > max_unique:
            max_word = word
            max_unique = unique_count
        elif unique_count == max_unique and word < max_word:
            max_word = word
    
    return max_word