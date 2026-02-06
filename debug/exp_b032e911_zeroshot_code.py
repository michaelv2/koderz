def Strongest_Extension(class_name, extensions):
    def calculate_strength(extension):
        cap = sum(1 for c in extension if c.isupper())
        sm = sum(1 for c in extension if c.islower())
        return cap - sm
    
    max_strength = float('-inf')
    strongest_extension = None
    
    for extension in extensions:
        strength = calculate_strength(extension)
        if strength > max_strength:
            max_strength = strength
            strongest_extension = extension
    
    return f"{class_name}.{strongest_extension}"