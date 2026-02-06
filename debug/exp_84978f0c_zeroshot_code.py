def do_algebra(operator, operand):
    expr = str(operand[0])
    for op, val in zip(operator, operand[1:]):
        expr += op + str(val)
    return eval(expr)