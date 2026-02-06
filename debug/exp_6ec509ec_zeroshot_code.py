def decimal_to_binary(decimal):
    # Convert decimal to binary using bin() function and remove '0b' prefix
    binary = bin(decimal)[2:]
    # Add 'db' at both ends of the binary string and return it
    return "db" + binary + "db"