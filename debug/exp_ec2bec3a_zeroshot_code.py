def fibfib(n: int):
    """Compute the n-th FibFib number where
    fibfib(0)=0, fibfib(1)=0, fibfib(2)=1 and
    fibfib(n)=fibfib(n-1)+fibfib(n-2)+fibfib(n-3) for n>=3.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0 or n == 1:
        return 0
    if n == 2:
        return 1

    # 3x3 matrix exponentiation
    def mat_mult(A, B):
        # multiply two 3x3 matrices
        return [
            [A[0][0]*B[0][0] + A[0][1]*B[1][0] + A[0][2]*B[2][0],
             A[0][0]*B[0][1] + A[0][1]*B[1][1] + A[0][2]*B[2][1],
             A[0][0]*B[0][2] + A[0][1]*B[1][2] + A[0][2]*B[2][2]],
            [A[1][0]*B[0][0] + A[1][1]*B[1][0] + A[1][2]*B[2][0],
             A[1][0]*B[0][1] + A[1][1]*B[1][1] + A[1][2]*B[2][1],
             A[1][0]*B[0][2] + A[1][1]*B[1][2] + A[1][2]*B[2][2]],
            [A[2][0]*B[0][0] + A[2][1]*B[1][0] + A[2][2]*B[2][0],
             A[2][0]*B[0][1] + A[2][1]*B[1][1] + A[2][2]*B[2][1],
             A[2][0]*B[0][2] + A[2][1]*B[1][2] + A[2][2]*B[2][2]],
        ]

    def mat_pow(mat, exp):
        # identity matrix
        result = [[1,0,0],[0,1,0],[0,0,1]]
        base = mat
        while exp > 0:
            if exp & 1:
                result = mat_mult(result, base)
            base = mat_mult(base, base)
            exp >>= 1
        return result

    # transformation matrix
    M = [[1,1,1],
         [1,0,0],
         [0,1,0]]

    # We want M^(n-2) * [f(2), f(1), f(0)]^T
    P = mat_pow(M, n-2)
    f2, f1, f0 = 1, 0, 0
    # result vector first component = P[0][0]*f2 + P[0][1]*f1 + P[0][2]*f0
    return P[0][0]*f2 + P[0][1]*f1 + P[0][2]*f0