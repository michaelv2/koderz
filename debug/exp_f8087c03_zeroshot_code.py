def decimal_to_binary(decimal):
    """Convert an integer to a binary string wrapped with 'db' at both ends."""
    # Handle zero explicitly
    if decimal == 0:
        return "db0db"
    # Handle negative numbers by preserving the minus sign
    if decimal < 0:
        return "db-" + bin(-decimal)[2:] + "db"
    return "db" + bin(decimal)[2:] + "db"