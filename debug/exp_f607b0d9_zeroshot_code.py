def string_to_md5(text):
    """
    Given a string 'text', return its md5 hash equivalent string.
    If 'text' is an empty string, return None.
    """
    import hashlib
    if text == "":
        return None
    # Ensure text is a str; encode to utf-8 for hashing
    if not isinstance(text, str):
        text = str(text)
    return hashlib.md5(text.encode('utf-8')).hexdigest()