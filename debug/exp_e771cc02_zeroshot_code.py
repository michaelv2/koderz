def Strongest_Extension(class_name, extensions):
    best_ext = None
    best_strength = None
    for ext in extensions:
        cap = sum(1 for c in ext if c.isupper())
        low = sum(1 for c in ext if c.islower())
        strength = cap - low
        if best_strength is None or strength > best_strength:
            best_strength = strength
            best_ext = ext
    return f"{class_name}.{best_ext}"