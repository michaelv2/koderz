def do_algebra(operator, operand):
    expr = str(operand[0])
    for i, op in enumerate(operator):
        expr += f" {op} {operand[i + 1]}"
    return eval(expr, {"__builtins__": {}} , {})