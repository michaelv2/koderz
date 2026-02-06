def check_dict_case(d):
    """
    Return True if all keys in the given dict are strings and all keys are either
    in lower-case form or in upper-case form. Return False for an empty dict.
    """
    if not isinstance(d, dict) or len(d) == 0:
        return False

    if any(not isinstance(k, str) for k in d.keys()):
        return False

    keys = list(d.keys())
    is_all_lower = all(k == k.lower() for k in keys)
    is_all_upper = all(k == k.upper() for k in keys)

    return is_all_lower or is_all_upper