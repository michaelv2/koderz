def bf(planet1, planet2):
    planets = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
    try:
        i1 = planets.index(planet1)
        i2 = planets.index(planet2)
    except ValueError:
        return ()
    if i1 == i2:
        return ()
    lo, hi = sorted((i1, i2))
    if hi - lo <= 1:
        return ()
    return tuple(planets[lo + 1 : hi])