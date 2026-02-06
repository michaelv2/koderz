def is_bored(S):
    import re
    
    # Split by sentence delimiters
    sentences = re.split(r'[.?!]+', S)
    
    count = 0
    for sentence in sentences:
        # Strip whitespace and check if it's not empty
        sentence = sentence.strip()
        if sentence and sentence.startswith('I'):
            count += 1
    
    return count