def bf(planet1, planet2):
    planets = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
    
    try:
        index1 = planets.index(planet1)
        index2 = planets.index(planet2)
    except ValueError:
        return ()
    
    # If same planet, return empty tuple
    if index1 == index2:
        return ()
    
    # Get the range between the two planets
    start_index = min(index1, index2)
    end_index = max(index1, index2)
    
    # Return planets between (exclusive of the input planets)
    return tuple(planets[start_index + 1:end_index])