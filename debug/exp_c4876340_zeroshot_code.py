def valid_date(date):
    # Check if date string is not empty
    if not date:
        return False
    
    # Check if format is correct (should have exactly 2 hyphens and be in mm-dd-yyyy format)
    parts = date.split('-')
    if len(parts) != 3:
        return False
    
    month_str, day_str, year_str = parts
    
    # Check if each part has correct length and is numeric
    if len(month_str) != 2 or len(day_str) != 2 or len(year_str) != 4:
        return False
    
    if not (month_str.isdigit() and day_str.isdigit() and year_str.isdigit()):
        return False
    
    month = int(month_str)
    day = int(day_str)
    year = int(year_str)
    
    # Check if month is valid (1-12)
    if month < 1 or month > 12:
        return False
    
    # Check if day is valid based on month
    if month in [1, 3, 5, 7, 8, 10, 12]:  # 31 days
        if day < 1 or day > 31:
            return False
    elif month in [4, 6, 9, 11]:  # 30 days
        if day < 1 or day > 30:
            return False
    elif month == 2:  # February - max 29 days
        if day < 1 or day > 29:
            return False
    
    return True