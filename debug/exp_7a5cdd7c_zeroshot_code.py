def check_dict_case(dict):
    if not dict:
        return False
    keys = list(dict.keys())
    for k in keys:
        if not isinstance(k, str):
            return False
    all_lower = all(k == k.lower() for k in keys)
    all_upper = all(k == k.upper() for k in keys)
    return all_lower or all_upper