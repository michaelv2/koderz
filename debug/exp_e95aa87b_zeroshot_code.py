def by_length(arr):
    names = {
        1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five",
        6: "Six", 7: "Seven", 8: "Eight", 9: "Nine"
    }
    # Keep only values between 1 and 9, sort ascending, then reverse
    vals = sorted(x for x in arr if isinstance(x, int) and 1 <= x <= 9)
    vals.reverse()
    return [names[x] for x in vals]