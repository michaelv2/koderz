def Strongest_Extension(class_name, extensions):
    # Initialize variables to keep track of the strongest extension and its strength
    strongest_extension = ''
    max_strength = 0
    
    for ext in extensions:
        # Calculate the strength of the current extension
        CAP = sum(1 for c in ext if c.isupper())
        SM = sum(1 for c in ext if c.islower())
        strength = CAP - SM
        
        # If this is the strongest extension so far, update our variables
        if strength > max_strength:
            max_strength = strength
            strongest_extension = ext
    
    return class_name + '.' + strongest_extension