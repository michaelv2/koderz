def factorial(num):
    """Helper function to calculate the factorial of a given number."""
    if num == 0 or num == 1:
        return 1
    result = 1
    for i in range(2, num + 1):
        result *= i
    return result

def special_factorial(n):
    """Calculate the Brazilian factorial of n."""
    brazilian_fact = 1
    for i in range(1, n + 1):
        brazilian_fact *= factorial(i)
    return brazilian_fact