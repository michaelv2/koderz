def bf(planet1, planet2):
    planets = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
    if planet1 not in planets or planet2 not in planets:
        return tuple()
    i1 = planets.index(planet1)
    i2 = planets.index(planet2)
    lo, hi = min(i1, i2), max(i1, i2)
    return tuple(planets[lo+1:hi])