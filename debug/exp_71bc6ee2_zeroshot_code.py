def words_string(s):
    if s is None:
        return []
    return s.replace(',', ' ').split()