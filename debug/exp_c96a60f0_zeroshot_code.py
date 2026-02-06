def Strongest_Extension(class_name, extensions):
    best = None
    best_strength = None
    for ext in extensions:
        cap = 0
        sm = 0
        for ch in ext:
            if 'A' <= ch <= 'Z':
                cap += 1
            elif 'a' <= ch <= 'z':
                sm += 1
        strength = cap - sm
        if best is None or strength > best_strength:
            best = ext
            best_strength = strength
    return f"{class_name}.{best}"