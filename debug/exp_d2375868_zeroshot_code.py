def Strongest_Extension(class_name, extensions):
    """You will be given the name of a class (a string) and a list of extensions.
    The extensions are to be used to load additional classes to the class. The
    strength of the extension is as follows: Let CAP be the number of the uppercase
    letters in the extension's name, and let SM be the number of lowercase letters 
    in the extension's name, the strength is given by the fraction CAP - SM. 
    You should find the strongest extension and return a string in this 
    format: ClassName.StrongestExtensionName.
    If there are two or more extensions with the same strength, you should
    choose the one that comes first in the list.
    """
    best_idx = -1
    best_strength = None
    for i, ext in enumerate(extensions):
        caps = sum(1 for c in ext if 'A' <= c <= 'Z')
        lowers = sum(1 for c in ext if 'a' <= c <= 'z')
        strength = caps - lowers
        if best_strength is None or strength > best_strength:
            best_strength = strength
            best_idx = i
    if best_idx == -1:
        return class_name + '.'
    return class_name + '.' + extensions[best_idx]