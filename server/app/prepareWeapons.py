from app import mongo

weaponsCollection = mongo.db.weapons

class PrepareWeaponException(Exception):
    pass

def set_prepared_weapons(character, selected_weapons):
    prepared_weapons = list()
    weapons_list = list()

    # Check if there is a shield in the selected_weapons.
    if 'shield' in selected_weapons or 'shield' in character['equipped']:
        if 'shield' in character['armor']:
            prepared_weapons.append('shield')

    # Count how many weapons the player has selected.
    for weapon in selected_weapons:
        if weapon != 'shield':
            weapons_list.append(weapon)

    # Check if player has selected too many weapons with shield.
    if len(weapons_list) > 1 and 'shield' in prepared_weapons:
        raise PrepareWeaponException("You cannot choose those weapons with a shield equipped.")
    elif len(weapons_list) == 1 and 'shield' in prepared_weapons:
        # Retrieve the weapon information from the database.
        weapon = weaponsCollection.find_one({'name': weapons_list[0]})

        # If weapon is can be held with one hand.
        if 'two_handed' not in weapon['properties']:
            prepared_weapons.append(weapon['name'])
        else:
            raise PrepareWeaponException("You cannot equip a two-handed weapon with a shield.")
    elif len(weapons_list) > 2:
        raise PrepareWeaponException("You can only have one weapon for each hand.")
    elif len(weapons_list) == 1:
        prepared_weapons.append(weapons_list[0])
    elif len(weapons_list) == 2:
        # Retrieve the weapons from the database.
        weapon1 = weaponsCollection.find_one({'name': weapons_list[0]})
        weapon2 = weaponsCollection.find_one({'name': weapons_list[1]})

        # Check if both weapons selected are two handed.
        if 'two_handed' in weapon1['properties'] and 'two_handed' in weapon2['properties']:
            raise PrepareWeaponException("You cannot equip two two-handed weapons.")
        elif 'two_handed' in weapon1['properties'] or 'two_handed' in weapon2['properties']:
            raise PrepareWeaponException("You cannot equip another weapon, if one is two-handed")
        else:
            prepared_weapons.append(weapon1['name'])
            prepared_weapons.append(weapon2['name'])

    return prepared_weapons
