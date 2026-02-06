def check_if_last_char_is_a_letter(txt):
    if not txt:
        return False
    if not txt[-1].isalpha():
        return False
    return len(txt) == 1 or txt[-2] == ' '