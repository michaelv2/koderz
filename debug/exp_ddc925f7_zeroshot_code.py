def bf(planet1, planet2):
    planets = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
    try:
        i = planets.index(planet1)
        j = planets.index(planet2)
    except ValueError:
        return ()
    a, b = min(i, j), max(i, j)
    if b - a <= 1:
        return ()
    return tuple(planets[a+1:b])