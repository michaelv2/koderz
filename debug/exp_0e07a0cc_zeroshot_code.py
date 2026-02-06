def eat(number, need, remaining):
    """
    Determine total eaten carrots and remaining after attempting to eat 'need' more,
    given 'remaining' carrots available.
    If not enough remaining, eat all remaining and be hungry.
    Returns [total_eaten, remaining_after].
    """
    eat_today = min(need, remaining)
    return [number + eat_today, remaining - eat_today]