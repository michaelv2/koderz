def make_a_pile(n):
    """
    Generate a list of n levels where the first level has n stones and each
    subsequent level increases by 2, preserving parity.
    """
    return [n + 2 * i for i in range(n)]