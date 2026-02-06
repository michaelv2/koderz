def correct_bracketing(brackets: str) -> bool:
    cnt = 0
    for ch in brackets:
        if ch == "<":
            cnt += 1
        elif ch == ">":
            cnt -= 1
            if cnt < 0:
                return False
    return cnt == 0