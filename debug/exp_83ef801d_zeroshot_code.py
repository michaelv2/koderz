def Strongest_Extension(class_name, extensions):
    strongest_extension = ''
    max_strength = float('-inf')
    
    for extension in extensions:
        cap = sum(1 for char in extension if char.isupper())
        sm = sum(1 for char in extension if char.islower())
        strength = cap - sm
        
        if strength > max_strength:
            max_strength = strength
            strongest_extension = extension
    
    return f'{class_name}.{strongest_extension}'