def valid_date(date):
    # Check if the date string is empty
    if not date:
        return False
    
    # Split the date string by '-'
    parts = date.split('-')
    
    # Check if the date has exactly three parts
    if len(parts) != 3:
        return False
    
    try:
        month, day, year = map(int, parts)
    except ValueError:
        return False
    
    # Check if the month is valid
    if month < 1 or month > 12:
        return False
    
    # Check if the day is valid for the given month
    if month in {1, 3, 5, 7, 8, 10, 12}:
        if day < 1 or day > 31:
            return False
    elif month in {4, 6, 9, 11}:
        if day < 1 or day > 30:
            return False
    elif month == 2:
        if day < 1 or day > 29:
            return False
    
    # If all checks pass, the date is valid
    return True