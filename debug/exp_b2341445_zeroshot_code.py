import re

def is_bored(S):
    sentences = re.split('[.?!]', S)
    boredoms = 0
    for sentence in sentences:
        if sentence.strip().startswith("I"):
            boredoms += 1
    return boredoms