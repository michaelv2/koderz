def check_if_last_char_is_a_letter(txt):
    txt = txt.rstrip()  # Remove trailing spaces
    if len(txt) > 0 and (txt[-1].isalpha()) and (len(txt) == 1 or txt[-2] == ' '):
        return True
    else:
        return False