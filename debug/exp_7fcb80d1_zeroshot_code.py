def encode(message):
    """
    Encodes the message by swapping case and replacing vowels with the letter 2 places ahead.
    """
    mapping = {'a': 'c', 'e': 'g', 'i': 'k', 'o': 'q', 'u': 'w'}
    swapped = message.swapcase()
    result_chars = []
    for ch in swapped:
        low = ch.lower()
        if low in mapping:
            rep = mapping[low]
            if ch.isupper():
                rep = rep.upper()
            result_chars.append(rep)
        else:
            result_chars.append(ch)
    return ''.join(result_chars)