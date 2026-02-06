def any_int(x, y, z):
    def is_integer_value(v):
        if isinstance(v, bool):
            return False
        if isinstance(v, int):
            return True
        if isinstance(v, float):
            return v.is_integer()
        return False

    if not (is_integer_value(x) and is_integer_value(y) and is_integer_value(z)):
        return False

    xi, yi, zi = int(x), int(y), int(z)
    return xi == yi + zi or yi == xi + zi or zi == xi + yi