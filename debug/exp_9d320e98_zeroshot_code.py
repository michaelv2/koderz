def valid_date(date):
    """Validates a date string in mm-dd-yyyy format."""
    
    # Rule 1: Check if date string is not empty
    if not date:
        return False
    
    # Rule 4: Check format (mm-dd-yyyy with hyphens)
    parts = date.split('-')
    if len(parts) != 3:
        return False
    
    month_str, day_str, year_str = parts
    
    # Validate format: mm, dd, yyyy
    if len(month_str) != 2 or len(day_str) != 2 or len(year_str) != 4:
        return False
    
    # Check if all parts are numeric
    if not (month_str.isdigit() and day_str.isdigit() and year_str.isdigit()):
        return False
    
    month = int(month_str)
    day = int(day_str)
    
    # Rule 3: Validate month is between 1 and 12
    if month < 1 or month > 12:
        return False
    
    # Rule 2: Validate day based on month
    days_in_month = {
        1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30,
        7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
    }
    
    max_days = days_in_month[month]
    if day < 1 or day > max_days:
        return False
    
    return True