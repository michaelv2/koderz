def bf(planet1, planet2):
    planets = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
    if planet1 not in planets or planet2 not in planets:
        return ()
    i1, i2 = planets.index(planet1), planets.index(planet2)
    if i1 == i2:
        return ()
    a, b = (i1, i2) if i1 < i2 else (i2, i1)
    return tuple(planets[a+1:b])