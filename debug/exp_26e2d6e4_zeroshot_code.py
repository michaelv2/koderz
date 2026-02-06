def order_by_points(nums):
    """
    Sort numbers by the sum of their digits (of their absolute value) in ascending order.
    If two numbers have the same digit sum, preserve their original order.
    """
    def digit_sum(n):
        n = abs(n)
        s = 0
        if n == 0:
            return 0
        while n:
            s += n % 10
            n //= 10
        return s

    indexed = [(i, v, digit_sum(v)) for i, v in enumerate(nums)]
    indexed.sort(key=lambda t: (t[2], t[0]))
    return [v for _, v, _ in indexed]