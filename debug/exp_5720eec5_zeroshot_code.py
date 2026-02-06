def check_dict_case(d):
    if not d:  # If the dictionary is empty, return False
        return False
    all_lower = all_upper = True
    for key in d:
        if not isinstance(key, str):  # If the key is not a string, return False
            return False
        if not key.islower():  # If the key is not all lowercase, set all_lower to False
            all_lower = False
        if not key.isupper():  # If the key is not all uppercase, set all_upper to False
            all_upper = False
    return all_lower or all_upper  # Return True if either all keys are lowercase or all keys are uppercase