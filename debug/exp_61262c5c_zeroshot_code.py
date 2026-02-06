def is_bored(S):
    import re
    
    # Split the string into sentences using regex to match '.', '?', or '!'
    sentences = re.split(r'[.?!]\s*', S)
    
    # Count the number of sentences that start with "I"
    boredom_count = sum(sentence.startswith("I") for sentence in sentences if sentence)
    
    return boredom_count