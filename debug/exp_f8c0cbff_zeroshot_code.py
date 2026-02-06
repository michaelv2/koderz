def encrypt(s):
    """Shift lowercase letters by +4 with wrap-around; non-lowercase chars unchanged."""
    a = ord('a')
    z = ord('z')
    res = []
    for ch in s:
        o = ord(ch)
        if a <= o <= z:
            res.append(chr(a + ((o - a + 4) % 26)))
        else:
            res.append(ch)
    return ''.join(res)