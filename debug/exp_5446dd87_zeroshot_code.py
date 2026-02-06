def is_bored(S):
    import re
    return len(re.findall(r'(?:^|[.?!]\s*)I\b', S))