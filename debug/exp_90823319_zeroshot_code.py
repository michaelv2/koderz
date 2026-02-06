def do_algebra(operator, operand):
    expr_parts = []
    for i, op in enumerate(operator):
        expr_parts.append(str(operand[i]))
        expr_parts.append(op)
    expr_parts.append(str(operand[-1]))
    expr = ''.join(expr_parts)
    return eval(expr)