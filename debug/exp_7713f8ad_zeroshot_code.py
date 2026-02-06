def check_dict_case(dict):
    if not dict:
        return False
    
    # Check if all keys are strings
    if not all(isinstance(key, str) for key in dict.keys()):
        return False
    
    # Get all string keys
    string_keys = [key for key in dict.keys() if isinstance(key, str)]
    
    # Check if all keys are lowercase or all keys are uppercase
    all_lower = all(key.islower() for key in string_keys)
    all_upper = all(key.isupper() for key in string_keys)
    
    return all_lower or all_upper