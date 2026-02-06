def encode_cyclic(s: str) -> str:
    # Split string into groups of three characters
    groups = [s[i:i+3] for i in range(0, len(s), 3)]
    # Cycle elements in each group
    encoded_groups = [group[-1] + group[:-1] if len(group) == 3 else group for group in groups]
    return "".join(encoded_groups)

def decode_cyclic(s: str) -> str:
    # Split string into groups of three characters
    groups = [s[i:i+3] for i in range(0, len(s), 3)]
    # Decode each group by moving the last character to the beginning
    decoded_groups = [group[1:] + group[0] if len(group) == 3 else group for group in groups]
    return "".join(decoded_groups)