def get_max_triples(n):
    # Create the array 'a' with values as per the problem statement
    a = [i * i - i + 1 for i in range(1, n+1)]
    
    count = 0
    # Iterate over all possible triplets of elements from 'a'
    for i in range(n):
        for j in range(i+1, n):
            for k in range(j+1, n):
                # Check if the sum of the current triplet is a multiple of 3
                if (a[i] + a[j] + a[k]) % 3 == 0:
                    count += 1
    return count