def largest_smallest_integers(lst):
    negatives = [i for i in lst if i < 0]
    positives = [i for i in lst if i > 0]
    
    a = max(negatives) if negatives else None
    b = min(positives) if positives else None
    
    return (a, b)