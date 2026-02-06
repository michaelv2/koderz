def compare_one(a, b):
    def parse_value(value):
        if isinstance(value, str):
            value = value.replace(',', '.')
            try:
                return float(value)
            except ValueError:
                return None
        return float(value)

    parsed_a = parse_value(a)
    parsed_b = parse_value(b)

    if parsed_a > parsed_b:
        return a
    elif parsed_b > parsed_a:
        return b
    else:
        return None