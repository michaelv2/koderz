import heapq

def maximum(arr, k):
    # Use heapq.nlargest to get the k largest elements
    largest_k = heapq.nlargest(k, arr)
    # Sort the k largest elements before returning
    return sorted(largest_k)