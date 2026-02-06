def decimal_to_binary(decimal):
    # Convert the decimal number to binary and remove the '0b' prefix
    binary = bin(decimal)[2:]
    
    # Format the binary string with 'db' at the beginning and end
    formatted_binary = f"db{binary}db"
    
    return formatted_binary