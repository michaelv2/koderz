def will_it_fly(q, w):
    if not isinstance(q, list):
        return False
    try:
        total = sum(q)
    except Exception:
        return False
    return q == q[::-1] and total <= w