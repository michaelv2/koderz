def check_dict_case(d):
    if not d:
        return False
    
    lower_case = upper_case = None
    
    for key in d.keys():
        if not isinstance(key, str):
            return False
        
        if lower_case is None and upper_case is None:
            lower_case = key.islower()
            upper_case = key.isupper()
        elif (lower_case and not key.islower()) or (upper_case and not key.isupper()):
            return False
    
    return True