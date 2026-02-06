def closest_integer(value):
    from decimal import Decimal, ROUND_HALF_UP
    d = Decimal(value)
    return int(d.quantize(Decimal('1'), rounding=ROUND_HALF_UP))