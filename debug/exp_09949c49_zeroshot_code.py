def Strongest_Extension(class_name, extensions):
    def strength(extension):
        upper = sum(1 for c in extension if c.isupper())
        lower = sum(1 for c in extension if c.islower())
        return upper - lower
    
    strongest_ext = max(extensions, key=strength)
    return f"{class_name}.{strongest_ext}"