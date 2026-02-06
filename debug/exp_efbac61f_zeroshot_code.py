def is_bored(S):
    import re
    parts = re.split(r'[.?!]', S)
    count = 0
    for p in parts:
        p = p.strip()
        if not p:
            continue
        first = p.split()[0]
        # strip non-letters from start and end (keep internal characters like apostrophes)
        first_clean = re.sub(r'^[^A-Za-z]+|[^A-Za-z]+$', '', first)
        if first_clean == 'I':
            count += 1
    return count