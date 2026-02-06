def valid_date(date):
    if not isinstance(date, str) or not date:
        return False
    if len(date) != 10:
        return False
    if date[2] != '-' or date[5] != '-':
        return False

    mm, dd, yyyy = date[:2], date[3:5], date[6:]

    if not (mm.isdigit() and dd.isdigit() and yyyy.isdigit()):
        return False

    month = int(mm)
    day = int(dd)

    if month < 1 or month > 12:
        return False

    if month in (1, 3, 5, 7, 8, 10, 12):
        max_day = 31
    elif month in (4, 6, 9, 11):
        max_day = 30
    elif month == 2:
        max_day = 29
    else:
        return False

    if day < 1 or day > max_day:
        return False

    return True