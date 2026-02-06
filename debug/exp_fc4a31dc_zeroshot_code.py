def check_dict_case(dict):
    if not dict:
        return False
    all_lower = True
    all_upper = True
    for k in dict.keys():
        if not isinstance(k, str):
            return False
        if k != k.lower():
            all_lower = False
        if k != k.upper():
            all_upper = False
        if not all_lower and not all_upper:
            return False
    return all_lower or all_upper