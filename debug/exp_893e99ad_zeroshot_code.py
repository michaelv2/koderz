def bf(planet1, planet2):
    planets = ("Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune")
    
    # Check if both planets are valid
    if planet1 not in planets or planet2 not in planets:
        return ()
    
    # Get indices of both planets
    index1 = planets.index(planet1)
    index2 = planets.index(planet2)
    
    # Get the range between them (handle both orderings)
    start = min(index1, index2)
    end = max(index1, index2)
    
    # Return planets between them (excluding the two input planets)
    return planets[start + 1:end]