def check_if_last_char_is_a_letter(txt):
    txt = txt.rstrip()
    if not txt:
        return False
    words = txt.split()
    return len(words[-1]) == 1 and words[-1].isalpha()