def encode(message):
    swapped = message.swapcase()
    result = []
    for ch in swapped:
        if ch.lower() in 'aeiou':
            lower = ch.lower()
            idx = ord(lower) - ord('a')
            new_idx = (idx + 2) % 26
            new_char = chr(ord('a') + new_idx)
            if ch.isupper():
                new_char = new_char.upper()
            result.append(new_char)
        else:
            result.append(ch)
    return ''.join(result)