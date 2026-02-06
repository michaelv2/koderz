def get_odd_collatz(n):
    def collatz_sequence(num):
        seq = [num]
        while num != 1:
            if num % 2 == 0:
                num //= 2
            else:
                num = 3 * num + 1
            seq.append(num)
        return seq

    collatz_seq = collatz_sequence(n)
    odd_collatz_seq = sorted([num for num in collatz_seq if num % 2 != 0])
    return odd_collatz_seq