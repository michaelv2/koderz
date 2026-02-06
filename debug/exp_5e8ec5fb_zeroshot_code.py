def is_bored(S):
    count = 0
    i = 0
    n = len(S)
    while i < n:
        # skip leading whitespace of a sentence
        while i < n and S[i].isspace():
            i += 1
        if i >= n:
            break

        # find end of the sentence delimited by ., ?, or !
        j = i
        while j < n and S[j] not in '.?!':
            j += 1

        sentence = S[i:j]

        # find the first word of the sentence
        p = 0
        while p < len(sentence) and sentence[p].isspace():
            p += 1
        if p < len(sentence):
            q = p
            while q < len(sentence) and not sentence[q].isspace():
                q += 1
            first = sentence[p:q]
            if first == 'I':
                count += 1

        # move to the character after the delimiter, if any
        if j < n:
            i = j + 1
        else:
            i = j
    return count