def car_race_collision(n: int):
    """
    There are n cars moving left-to-right and n cars moving right-to-left on an infinite line.
    With equal speeds and no change in trajectories upon collision, every pair of cars
    from opposite directions will collide exactly once.
    Therefore, the total number of collisions is n * n.
    """
    return n * n