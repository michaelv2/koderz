def decimal_to_binary(decimal):
    binary_str = bin(decimal)[2:]  # Convert to binary and remove the '0b' prefix
    return f"db{binary_str}db"     # Format with 'db' at the beginning and end