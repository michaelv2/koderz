def compare_one(a, b):
    def to_num(x):
        if isinstance(x, str):
            s = x.strip()
            # If both separators present, decide which is decimal by last occurrence
            if '.' in s and ',' in s:
                if s.rfind(',') > s.rfind('.'):
                    # comma is decimal separator, remove dots (thousands), convert comma to dot
                    s = s.replace('.', '')
                    s = s.replace(',', '.')
                else:
                    # dot is decimal separator, remove commas (thousands)
                    s = s.replace(',', '')
            else:
                # Single type: treat comma as decimal separator
                s = s.replace(',', '.')
            return float(s)
        else:
            # int, float, bool handled by float()
            return float(x)
    a_num = to_num(a)
    b_num = to_num(b)
    if a_num > b_num:
        return a
    if b_num > a_num:
        return b
    return None