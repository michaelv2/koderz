def decimal_to_binary(decimal):
    """Convert an integer to its binary representation wrapped with 'db' at both ends."""
    # Handle sign
    if decimal == 0:
        return "db0db"
    sign = ''
    if decimal < 0:
        sign = '-'
        decimal = -decimal
    # Use Python formatting to get binary without '0b' prefix
    binary = format(decimal, 'b')
    return f"db{sign}{binary}db"