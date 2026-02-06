def do_algebra(operator, operand):
    # Start with the first operand
    expression = str(operand[0])
    
    # Interleave operators and operands
    for i in range(len(operator)):
        expression += f" {operator[i]} {operand[i + 1]}"
    
    # Evaluate the constructed expression
    return eval(expression)