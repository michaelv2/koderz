def sort_third(l: list):
    l_prime = []
    for i in range(len(l)):
        if i % 3 == 0:
            sorted_value = sorted([l[i]])[0]
            l_prime.append(sorted_value)
        else:
            l_prime.append(l[i])
    return l_prime