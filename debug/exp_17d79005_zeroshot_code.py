def sort_third(l: list):
    third_elements = [l[i] for i in range(2, len(l), 3)]
    third_elements.sort()
    sorted_list = l[:]
    for i, element in enumerate(third_elements):
        sorted_list[(i * 3) + 2] = element
    return sorted_list