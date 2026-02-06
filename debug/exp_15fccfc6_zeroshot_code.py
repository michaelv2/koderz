def encode(message):
    result = []
    for ch in message:
        if ch.isalpha():
            swapped = ch.swapcase()
            lower = swapped.lower()
            if lower in 'aeiou':
                ahead = chr(ord(lower) + 2)
                swapped = ahead.upper() if swapped.isupper() else ahead
            result.append(swapped)
        else:
            result.append(ch)
    return ''.join(result)