def valid_date(date):
    if not date:
        return False

    components = date.split('-')
    if len(components) != 3:
        return False

    try:
        month, day, year = map(int, components)
    except ValueError:
        return False

    if month < 1 or month > 12:
        return False

    days_in_month = {
        1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30,
        7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
    }

    if day < 1 or day > days_in_month[month]:
        return False

    return True