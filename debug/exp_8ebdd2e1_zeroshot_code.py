def common(l1: list, l2: list) -> list:
    # Convert lists to sets
    set1 = set(l1)
    set2 = set(l2)

    # Find intersection of two sets
    common_elements = set1 & set2

    # Convert result back to a list and sort it
    sorted_common_elements = sorted(list(common_elements))

    return sorted_common_elements