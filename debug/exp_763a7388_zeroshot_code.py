def bf(planet1, planet2):
    planets = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
    try:
        i = planets.index(planet1)
        j = planets.index(planet2)
    except ValueError:
        return ()
    lo, hi = min(i, j), max(i, j)
    return tuple(planets[lo+1:hi])