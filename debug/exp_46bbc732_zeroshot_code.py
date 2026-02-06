def words_string(s):
    if not isinstance(s, str):
        s = str(s)
    s = s.replace(',', ' ')
    return s.split()