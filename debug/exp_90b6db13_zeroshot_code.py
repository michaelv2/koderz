from typing import List

def string_xor(a: str, b: str) -> str:
    # Initialize an empty result string
    result = ''
    
    # Iterate over the length of the strings
    for i in range(len(a)):
        # Perform XOR operation on each pair of corresponding characters from a and b
        xor_result = int(a[i]) ^ int(b[i])
        
        # Append the result to the result string
        result += str(xor_result)
    
    return result