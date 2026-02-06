def get_max_triples(n):
    # Generate the array a
    a = [i * i - i + 1 for i in range(1, n + 1)]

    # Initialize counter for valid triples
    count = 0

    # Iterate through all possible triples (i, j, k) where i < j < k
    for i in range(n - 2):
        for j in range(i + 1, n - 1):
            for k in range(j + 1, n):
                # Check if the sum of a[i], a[j], and a[k] is divisible by 3
                if (a[i] + a[j] + a[k]) % 3 == 0:
                    count += 1

    return count