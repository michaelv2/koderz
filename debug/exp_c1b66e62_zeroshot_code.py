def Strongest_Extension(class_name, extensions):
    max_strength = float('-inf')
    strongest_extension = None

    for extension in extensions:
        strength = sum(1 if c.isupper() else -1 for c in extension)
        if strength > max_strength:
            max_strength = strength
            strongest_extension = extension

    return f'{class_name}.{strongest_extension}'