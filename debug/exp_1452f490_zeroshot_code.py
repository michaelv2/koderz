def match_parens(lst):
    def is_balanced(s):
        stack = []
        for char in s:
            if char == '(':
                stack.append(char)
            elif char == ')':
                if not stack or stack[-1] != '(':
                    return False
                else:
                    stack.pop()
        return len(stack) == 0
    
    for i in range(2):
        for j in range(2):
            if is_balanced(lst[0][::((i*2)-1)] + lst[1][::((j*2)-1)]):
                return 'Yes'
    return 'No'