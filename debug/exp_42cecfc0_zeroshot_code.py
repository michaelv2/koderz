def decimal_to_binary(decimal):
    """Convert decimal to binary format with 'db' prefix and suffix."""
    return "db" + bin(decimal)[2:] + "db"