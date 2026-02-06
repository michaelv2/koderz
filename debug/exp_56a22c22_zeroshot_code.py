def bf(planet1, planet2):
    planets = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
    try:
        i = planets.index(planet1)
        j = planets.index(planet2)
    except ValueError:
        return ()
    if i == j:
        return ()
    start = min(i, j) + 1
    end = max(i, j)
    return tuple(planets[start:end])