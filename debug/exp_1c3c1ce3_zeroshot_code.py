from two integers, round it away from zero.
from two integers, the one you should return is the one that is the

from decimal import Decimal, ROUND_HALF_UP

def closest_integer(value):
    d = Decimal(str(value)).strip() if not isinstance(value, str) else value.strip()
    # Ensure we create Decimal from the string (avoid passing Decimal to str twice)
    dec = Decimal(d)
    rounded = dec.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return int(rounded)