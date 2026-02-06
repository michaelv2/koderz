def fibfib(n: int) -> int:
    """Compute the n-th term of the FibFib sequence defined by:
    fibfib(0) = 0, fibfib(1) = 0, fibfib(2) = 1,
    fibfib(n) = fibfib(n-1) + fibfib(n-2) + fibfib(n-3) for n >= 3.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0 or n == 1:
        return 0
    if n == 2:
        return 1

    def mat_mult(A, B):
        """Multiply two 3x3 matrices."""
        return [
            [
                A[0][0]*B[0][0] + A[0][1]*B[1][0] + A[0][2]*B[2][0],
                A[0][0]*B[0][1] + A[0][1]*B[1][1] + A[0][2]*B[2][1],
                A[0][0]*B[0][2] + A[0][1]*B[1][2] + A[0][2]*B[2][2],
            ],
            [
                A[1][0]*B[0][0] + A[1][1]*B[1][0] + A[1][2]*B[2][0],
                A[1][0]*B[0][1] + A[1][1]*B[1][1] + A[1][2]*B[2][1],
                A[1][0]*B[0][2] + A[1][1]*B[1][2] + A[1][2]*B[2][2],
            ],
            [
                A[2][0]*B[0][0] + A[2][1]*B[1][0] + A[2][2]*B[2][0],
                A[2][0]*B[0][1] + A[2][1]*B[1][1] + A[2][2]*B[2][1],
                A[2][0]*B[0][2] + A[2][1]*B[1][2] + A[2][2]*B[2][2],
            ],
        ]

    def mat_pow(A, power):
        """Exponentiate a 3x3 matrix A to the given integer power."""
        # Identity matrix
        result = [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
        ]
        base = [row[:] for row in A]
        p = power
        while p > 0:
            if p & 1:
                result = mat_mult(result, base)
            base = mat_mult(base, base)
            p >>= 1
        return result

    # Transition matrix for the recurrence:
    # [fib(n), fib(n-1), fib(n-2)]^T = A * [fib(n-1), fib(n-2), fib(n-3)]^T
    A = [
        [1, 1, 1],
        [1, 0, 0],
        [0, 1, 0],
    ]

    # fibfib(n) = (A^(n-2))[0][0] for n >= 2
    P = mat_pow(A, n - 2)
    return P[0][0]