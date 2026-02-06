def is_nested(string):
    opens = 0
    second_open_index = -1
    for i, ch in enumerate(string):
        if ch == '[':
            opens += 1
            if opens == 2:
                second_open_index = i
                break
    if second_open_index == -1:
        return False
    closes = 0
    for ch in string[second_open_index + 1:]:
        if ch == ']':
            closes += 1
            if closes >= 2:
                return True
    return False