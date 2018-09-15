def gen_combat_id(name, number_id):
    # Lowercase the name and remove spaces.
    combat_identifier = name.lower().replace(" ", "_")

    # Add the unique number at the end of the string.
    combat_identifier += str(number_id)

    return combat_identifier