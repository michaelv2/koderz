def is_nested(string):
    opens_found = 0
    second_open_index = None

    for idx, ch in enumerate(string):
        if ch == '[':
            if opens_found == 0:
                opens_found = 1
            elif opens_found == 1:
                second_open_index = idx
                break

    if second_open_index is None:
        return False

    closes_after = string[second_open_index + 1:].count(']')
    return closes_after >= 2