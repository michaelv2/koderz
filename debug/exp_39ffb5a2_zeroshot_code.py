def fibfib(n: int):
    """Compute the n-th element of the FibFib sequence efficiently using matrix exponentiation.

    Base cases:
        fibfib(0) = 0
        fibfib(1) = 0
        fibfib(2) = 1

    For n >= 3, fibfib(n) = fibfib(n-1) + fibfib(n-2) + fibfib(n-3).
    """
    if n <= 1:
        return 0
    if n == 2:
        return 1

    # Transition matrix for the recurrence:
    # [f(n), f(n-1), f(n-2)]^T = T * [f(n-1), f(n-2), f(n-3)]^T
    T = [
        [1, 1, 1],
        [1, 0, 0],
        [0, 1, 0]
    ]

    def mat_mul(A, B):
        C = [[0, 0, 0] for _ in range(3)]
        for i in range(3):
            for k in range(3):
                if A[i][k]:
                    aik = A[i][k]
                    bk = B[k]
                    C[i][0] += aik * bk[0]
                    C[i][1] += aik * bk[1]
                    C[i][2] += aik * bk[2]
        return C

    def mat_pow(M, e):
        # Identity matrix
        R = [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ]
        A = M
        while e > 0:
            if e & 1:
                R = mat_mul(R, A)
            A = mat_mul(A, A)
            e >>= 1
        return R

    P = mat_pow(T, n - 2)
    return P[0][0]