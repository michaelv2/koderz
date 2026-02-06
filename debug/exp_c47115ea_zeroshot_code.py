def histogram(test):
    s = test.strip()
    if not s:
        return {}
    counts = {}
    for token in s.split():
        counts[token] = counts.get(token, 0) + 1
    max_count = max(counts.values())
    return {k: v for k, v in counts.items() if v == max_count}