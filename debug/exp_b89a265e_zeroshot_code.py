def is_bored(S):
    import re
    parts = re.split(r'[.?!]', S)
    count = 0
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = re.search(r'\b([A-Za-z]+)\b', part)
        if m and m.group(1) == 'I':
            count += 1
    return count