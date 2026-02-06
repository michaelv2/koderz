def check_dict_case(d):
    if not d:
        return False
    
    all_lower = True
    all_upper = True
    
    for key in d.keys():
        if not isinstance(key, str):
            return False
        if not key.islower():
            all_lower = False
        if not key.isupper():
            all_upper = False
    
    return all_lower or all_upper