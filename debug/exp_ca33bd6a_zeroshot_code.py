def is_nested(string):
    count_opens = 0
    inner_closed = False
    for ch in string:
        if ch == '[':
            count_opens += 1
        elif ch == ']':
            if not inner_closed:
                if count_opens >= 2:
                    inner_closed = True
            else:
                return True
    return False