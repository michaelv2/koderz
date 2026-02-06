def fibfib(n: int):
    """Compute the n-th term of the fibfib sequence efficiently using matrix exponentiation."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0 or n == 1:
        return 0
    if n == 2:
        return 1

    # Transition matrix for F(n+1) = F(n) + F(n-1) + F(n-2)
    M = [
        [1, 1, 1],
        [1, 0, 0],
        [0, 1, 0]
    ]

    def mat_mult(A, B):
        res = [[0, 0, 0] for _ in range(3)]
        for i in range(3):
            for k in range(3):
                if A[i][k]:
                    a = A[i][k]
                    for j in range(3):
                        res[i][j] += a * B[k][j]
        return res

    def mat_pow(mat, power):
        # Identity matrix
        result = [[1 if i == j else 0 for j in range(3)] for i in range(3)]
        while power > 0:
            if power & 1:
                result = mat_mult(result, mat)
            mat = mat_mult(mat, mat)
            power >>= 1
        return result

    # F(n) = (M^(n-2))[0][0] since F(2)=1, F(1)=0, F(0)=0
    P = mat_pow(M, n - 2)
    return P[0][0]