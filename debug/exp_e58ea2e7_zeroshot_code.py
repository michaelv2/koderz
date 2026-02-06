def get_max_triples(n):
    # Count numbers based on their remainder when divided by 3
    count_remainder_0 = 0
    count_remainder_1 = 0
    
    for i in range(1, n + 1):
        value = i * i - i + 1
        remainder = value % 3
        if remainder == 0:
            count_remainder_0 += 1
        else:  # remainder == 1
            count_remainder_1 += 1
    
    # For three numbers to sum to multiple of 3, we need:
    # 1. Three numbers with remainder 0: C(count_remainder_0, 3)
    # 2. Three numbers with remainder 1: C(count_remainder_1, 3)  
    # 3. One each of remainder 0, 1, 2: count_remainder_0 * count_remainder_1 * count_remainder_2
    
    # But we only have remainders 0 and 1, so we need to be more careful
    # Actually, let me recompute the remainders properly
    
    # Recomputing properly:
    # a[i] = i*i - i + 1 = i*(i-1) + 1
    
    # Let's compute the actual counts
    count_0 = 0  # numbers with remainder 0
    count_1 = 0  # numbers with remainder 1
    
    for i in range(1, n + 1):
        a_i = i * i - i + 1
        if a_i % 3 == 0:
            count_0 += 1
        else:
            count_1 += 1
    
    # For sum to be divisible by 3:
    # Case 1: All three have remainder 0 -> C(count_0, 3)
    # Case 2: All three have remainder 1 -> C(count_1, 3)
    # Case 3: One each of 0, 1, 2 -> but we don't have remainder 2!
    
    # Let me double-check the pattern:
    # i=1: 1*1-1+1 = 1, remainder 1
    # i=2: 2*2-2+1 = 3, remainder 0  
    # i=3: 3*3-3+1 = 7, remainder 1
    # i=4: 4*4-4+1 = 13, remainder 1
    # i=5: 5*5-5+1 = 21, remainder 0
    
    # So we have: 1, 3, 7, 13, 21 with remainders 1, 0, 1, 1, 0
    # This means count_0 = 2, count_1 = 3
    
    # For combinations:
    # C(n,3) = n*(n-1)*(n-2)/6
    # C(2,3) = 0 (can't choose 3 from 2)
    # C(3,3) = 1
    
    result = 0
    
    # All three from remainder 0 group
    if count_0 >= 3:
        result += count_0 * (count_0 - 1) * (count_0 - 2) // 6
    
    # All three from remainder 1 group  
    if count_1 >= 3:
        result += count_1 * (count_1 - 1) * (count_1 - 2) // 6
    
    # This approach is wrong - we need to be more systematic
    
    # Let me just compute the array and count directly
    a = []
    for i in range(1, n + 1):
        a.append(i * i - i + 1)
    
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                if (a[i] + a[j] + a[k]) % 3 == 0:
                    count += 1
    
    return count