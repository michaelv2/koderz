def do_algebra(operator, operand):
    # Initialize the expression with the first operand
    expression = str(operand[0])
    
    # Iterate through the operators and operands to build the expression
    for i in range(len(operator)):
        expression += f" {operator[i]} {operand[i + 1]}"
    
    # Evaluate the constructed expression
    result = eval(expression)
    return result