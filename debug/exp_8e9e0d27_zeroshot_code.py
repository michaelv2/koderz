def is_bored(S):
    import re
    # Split by sentence delimiters (. ? !)
    sentences = re.split(r'[.!?]', S)
    
    count = 0
    for sentence in sentences:
        # Strip whitespace from the sentence
        trimmed = sentence.strip()
        # Check if sentence starts with "I" as a complete word
        if trimmed.startswith("I ") or trimmed == "I":
            count += 1
    
    return count