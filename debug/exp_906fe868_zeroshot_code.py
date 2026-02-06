def check_dict_case(dict):
    """
    Given a dictionary, return True if all keys are strings in lower 
    case or all keys are strings in upper case, else return False.
    The function should return False is the given dictionary is empty.
    """
    if not dict:
        return False
    
    # Check if all keys are strings
    if not all(isinstance(key, str) for key in dict.keys()):
        return False
    
    # Check if all keys are lowercase or all keys are uppercase
    keys = list(dict.keys())
    all_lower = all(key == key.lower() for key in keys)
    all_upper = all(key == key.upper() for key in keys)
    
    return all_lower or all_upper