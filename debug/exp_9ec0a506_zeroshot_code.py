def decimal_to_binary(decimal):
    """Convert an integer to its binary representation wrapped with 'db' prefixes/suffixes."""
    return "db" + format(decimal, "b") + "db"