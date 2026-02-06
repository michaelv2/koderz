def rounded_avg(n, m):
    if n > m:
        return -1
    total_sum = (m - n + 1) * (n + m) // 2
    count = m - n + 1
    average = round(total_sum / count)
    return bin(average)