def closest_integer(value):
    from decimal import Decimal, ROUND_FLOOR

    x = Decimal(value)
    floor_x = x.to_integral_value(rounding=ROUND_FLOOR)
    frac = x - floor_x
    half = Decimal('0.5')

    if frac > half:
        return int(floor_x + 1)
    elif frac < half:
        return int(floor_x)
    else:
        # Tie: away from zero
        return int(floor_x + 1) if x >= 0 else int(floor_x)