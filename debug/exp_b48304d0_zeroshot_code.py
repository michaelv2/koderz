def get_odd_collatz(n):
    def collatz(num):
        while num != 1:
            yield num
            num = num * 3 + 1 if num % 2 else num // 2
        yield num
    
    return sorted([i for i in set(collatz(n)) if i % 2])