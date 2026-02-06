def do_algebra(operator, operand):
    if not isinstance(operator, (list, tuple)) or not isinstance(operand, (list, tuple)):
        raise TypeError("operator and operand must be lists or tuples")
    if len(operand) != len(operator) + 1:
        raise ValueError("Length of operand must be one more than length of operator")

    parts = []
    for i, val in enumerate(operand):
        parts.append(str(val))
        if i < len(operator):
            parts.append(operator[i])
    expr = ' '.join(parts)

    result = eval(expr, {"__builtins__": None}, {})
    return int(result)