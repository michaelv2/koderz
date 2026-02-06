def do_algebra(operator, operand):
    # Create the expression by combining operands and operators
    expression = []
    for i in range(len(operand)):
        expression.append(str(operand[i]))
        if i < len(operator):
            expression.append(operator[i])
    
    # Convert to string and evaluate
    expr_str = ''.join(expression)
    
    # We need to be careful about operator precedence
    # Let's build it step by step with proper precedence
    
    # First, let's create a proper expression string
    result = operand[0]
    for i in range(len(operator)):
        if operator[i] == '+':
            result += operand[i+1]
        elif operator[i] == '-':
            result -= operand[i+1]
        elif operator[i] == '*':
            result *= operand[i+1]
        elif operator[i] == '//':
            result //= operand[i+1]
        elif operator[i] == '**':
            result **= operand[i+1]
    
    return result