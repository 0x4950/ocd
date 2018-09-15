def euclidean_distance(old_position, new_position):
    """
    Calculates the euclidean distance between two points in a 2D space.
    Returns an integer representing the distance in blocks of 5 ft.
    """
    if old_position == 0:
        p1 = (0, 0)
    else:
        p1 = divmod(old_position, 8)

    if new_position == 0:
        p2 = (0, 0)
    else:
        p2 = divmod(new_position, 8)

    distance = (abs(p1[0] - p2[0]) + (abs(p1[1] - p2[1]))) * 5

    return distance