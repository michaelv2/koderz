def check_dict_case(d):
    # If the dictionary is empty, return False
    if not d:
        return False
    
    # Check if all keys are strings
    for key in d.keys():
        if not isinstance(key, str):
            return False
            
    # Get first key and check case
    first_key = next(iter(d))
    if first_key.islower():
        # If the first key is lowercase, all keys should be lowercase
        for key in d.keys():
            if not key.islower():
                return False
    elif first_key.isupper():
        # If the first key is uppercase, all keys should be uppercase
        for key in d.keys():
            if not key.isupper():
                return False
                
    # If we've gone through all keys without returning False, all keys have the same case
    return True