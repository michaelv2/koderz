def valid_date(date):
    if not isinstance(date, str):
        return False
    s = date.strip()
    if not s:
        return False

    parts = s.split('-')
    if len(parts) != 3:
        return False

    m_s, d_s, y_s = parts
    if not (m_s.isdigit() and d_s.isdigit() and y_s.isdigit()):
        return False
    if len(y_s) != 4:
        return False

    month = int(m_s)
    day = int(d_s)

    if month < 1 or month > 12:
        return False

    if month in {1, 3, 5, 7, 8, 10, 12}:
        max_day = 31
    elif month in {4, 6, 9, 11}:
        max_day = 30
    else:  # February
        max_day = 29

    if day < 1 or day > max_day:
        return False

    return True