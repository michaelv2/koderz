from decimal import Decimal, ROUND_FLOOR

def closest_integer(value):
    val = Decimal(value)
    sign = 1 if val >= 0 else -1
    a = abs(val)
    floor_a = a.to_integral_value(rounding=ROUND_FLOOR)
    frac = a - floor_a
    if frac >= Decimal('0.5'):
        result_abs = floor_a + 1
    else:
        result_abs = floor_a
    result = sign * result_abs
    return int(result)