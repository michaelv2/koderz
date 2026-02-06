def car_race_collision(n: int):
    """
    Returns the number of collisions between n cars moving left-to-right and n cars moving right-to-left
    on an infinite straight road, where all cars have the same speed and collisions do not affect trajectories.
    Each pair of cars (one from each direction) collides exactly once, so the total number of collisions is n*n.
    """
    return n * n