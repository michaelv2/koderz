def numerical_letter_grade(grades):
    """Convert a list of numeric GPAs to letter grades according to the given table."""
    result = []
    for g in grades:
        try:
            val = float(g)
        except Exception:
            # If conversion fails, treat as E (safest fallback)
            result.append('E')
            continue
        if val >= 4.0:
            result.append('A+')
        elif val > 3.7:
            result.append('A')
        elif val > 3.3:
            result.append('A-')
        elif val > 3.0:
            result.append('B+')
        elif val > 2.7:
            result.append('B')
        elif val > 2.3:
            result.append('B-')
        elif val > 2.0:
            result.append('C+')
        elif val > 1.7:
            result.append('C')
        elif val > 1.3:
            result.append('C-')
        elif val > 1.0:
            result.append('D+')
        elif val > 0.7:
            result.append('D')
        elif val > 0.0:
            result.append('D-')
        else:
            result.append('E')
    return result