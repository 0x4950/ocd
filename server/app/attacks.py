from math import floor
from dice import roll
from . import spells
from pymongo import MongoClient
from config import uri

weapons_collection = db['weapons']

class PrepareWeaponException(Exception):
    pass

def attack_roll(actor, target, weapon, weapon_property, chars_distance):
    attack_status = None
    attack_roll_dice = 0
    attack_roll_result = 0  # Variable for the final returning result.
    has_disadvantage = False
    has_advantage = False
    attack_roll_bonus = 0

    # Roll 2 dice.
    attack_roll_dice1 = roll('1d20t')
    attack_roll_dice2 = roll('1d20t')

    # Check if character has lucky trait.
    if 'lucky' in actor['buffs']['attack_rolls']:
        if attack_roll_dice1 == 1:
            attack_roll_dice1 = roll('1d20t')

    # Check if ranged/thrown weapon is fired beyond normal range or within 5ft.
    if (weapon['attack_range'] == 'melee' and weapon_property == 'thrown') \
        or weapon['attack_range'] == 'ranged':
        if chars_distance > weapon['normal_range']:
            has_disadvantage = True
        elif chars_distance == 5:
            has_disadvantage = True

        # Also check for 'Archery' trait for ranged weapons.
        if 'archery' in actor['buffs']['attack_rolls']:
            attack_roll_result += 2

    # Check if character has heavy disadvantage.
    if actor['type'] == 'player_character':
        if 'heavy' in weapon['properties']:
            if 'heavy_disadvantage' in actor['debuffs']['attack_rolls']['disadvantages']:
                has_disadvantage = True
            elif 'armor_proficiency_lack' in actor['debuffs']['attack_rolls']['disadvantages']:
                has_disadvantage = True

    # If weapon has disadvantage, count the minimum dice roll.
    if has_disadvantage and not has_advantage:
        attack_roll_dice = min(attack_roll_dice1, attack_roll_dice2)
    elif has_advantage and not has_advantage:
        attack_roll_dice = max(attack_roll_dice1, attack_roll_dice2)
    else:
        attack_roll_dice = attack_roll_dice1

    attack_roll_result += attack_roll_dice

    if attack_roll_dice == 1:
        # Rolling 1
        attack_status = 'miss'
    elif attack_roll_dice == 20:
        # Rolling 20
        attack_status = 'critical'
    elif attack_roll_dice == 19 and 'improved_critical' in actor['buffs']['attack_rolls']:
        # Rolling 19, but having the Fighter 'Improved Critical' trait.
        attack_status = 'critical'
    else:
        # Add the proper ability modifier.
        actor_strength_ability_modifier = floor((actor['ability_scores']['strength'] - 10) / 2)
        actor_dexterity_ability_modifier = floor((actor['ability_scores']['dexterity'] - 10) / 2)

        if 'finesse' in weapon['properties'] or 'thrown' in weapon['properties']:
            # If weapon is finesse/thrown character's max[Strength, Dexterity] will be used.
            attack_roll_result += max(actor_strength_ability_modifier,
                                      actor_dexterity_ability_modifier)
        elif weapon['attack_range'] == 'melee':
            # If weapon is melee then character's strength modifier will be used.
            attack_roll_result += actor_strength_ability_modifier
        elif weapon['attack_range'] == 'ranged':
            # If weapon is ranged then character's dexterity modifier will be used.
            attack_roll_result += actor_dexterity_ability_modifier

        # Proficiency Bonus.
        if 'proficiencies' in actor:
            if 'weapons' in actor['proficiencies']:
                if weapon['name'] in actor['proficiencies']['weapons']:
                    attack_roll_result += actor['proficiency_bonus']

        # Temporary attack roll buffs.
        if 'attack_rolls' in actor['buffs']['temporary']:
            for buff in actor['buffs']['temporary']['attack_rolls']:
                if buff['type'] == 'dice_roll_add':
                    # Roll the appropriate dice defined by the buff.
                    attack_roll_bonus = roll(buff['dice'])

                    # Adding flat amount to the attack_roll_result.
                    attack_roll_result += attack_roll_bonus

        # Persistent attack roll buffs.
        if 'attack_rolls' in actor['buffs']:
            for buff in actor['buffs']['attack_rolls']:
                if isinstance(buff, dict):
                    if buff['type'] == 'flat':
                        # Adding flat amount to the attack_roll_result.
                        attack_roll_bonus = buff['amount']

                        attack_roll_result += attack_roll_bonus

        # Compare actor's attack roll with target's armor class.
        if attack_roll_result >= calculate_armor_class(target):
            attack_status = 'success'
        else:
            attack_status = 'miss'

    return attack_status

def damage_roll(actor, target, weapon, weapon_property, critical, bonus_action_attack):
    damage_roll_result = 0
    critical_modifier = 1

    # If hit was critical, get all of the attack's damage dice twice.
    if critical:
        critical_modifier = 2

    # Check which dice to use, according to weapon property.
    if weapon_property == 'versatile':
        damage_dice = weapon['versatile_die']
    else:
        damage_dice = weapon['damage_die']

    # Roll the damage roll dice
    for i in range(critical_modifier):
        damage_roll_result += roll(damage_dice + 't')

    # Check for Fighter's traits.
    if 'great_weapon_fighting' in actor['buffs']['damage_rolls']:
        if 'two_handed' in weapon['properties']:
            if damage_roll_result == 1 or damage_roll_result == 2:
                damage_roll_result = roll(damage_dice + 't')
    elif 'dueling' in actor['buffs']['damage_rolls']:
        if (weapon['attack_range'] == 'melee') and ('two_handed' not in weapon['properties']):
            if (not actor['action_used']) and (not bonus_action_attack):
                damage_roll_result += 2

    # If this is not a bonus action attack or the actor has the 'Two Weapon Fighting'
    # trait, then add the ability modifier to the damage roll result.
    if (not bonus_action_attack) or ('two-weapon-fighting' in actor['buffs']['damage_rolls']):
        actor_strength_ability_modifier = floor((actor['ability_scores']['strength'] - 10) / 2)
        actor_dexterity_ability_modifier = floor((actor['ability_scores']['dexterity'] - 10) / 2)

        if weapon_property == 'finesse' or weapon_property == 'thrown':
            damage_roll_result += max(actor_strength_ability_modifier,
                                      actor_dexterity_ability_modifier)
        elif weapon['attack_range'] == 'melee':
            # If weapon is melee then character's strength modifier will be used.
            damage_roll_result += actor_strength_ability_modifier
        elif weapon['attack_range'] == 'ranged':
            # If weapon is ranged then character's dexterity modifier will be used.
            damage_roll_result += actor_dexterity_ability_modifier

    return damage_roll_result

def death_saving_throw(character):
    has_advantage = False
    has_disadvantage = False
    death_saving_throw_roll_dice = 0

    # Check for saving throws temporary buffs.
    if 'death_saving_throws' in character['buffs']['temporary']:
        for buff in character['buffs']['temporary']['death_saving_throws']:
            if buff['type'] == 'advantage':
                has_advantage = True

    # Roll two dices.
    roll_dice1 = roll('1d20t')
    roll_dice2 = roll('1d20t')

    # Act according the advantages, disadvantages.
    if has_advantage and not has_disadvantage:
        death_saving_throw_roll_dice += max(roll_dice1, roll_dice2)
    elif has_disadvantage and not has_advantage:
        death_saving_throw_roll_dice += min(roll_dice1, roll_dice2)
    else:
        death_saving_throw_roll_dice += roll_dice1

    # Check whether or not the character succeeds the Death Saving Throw.
    if death_saving_throw_roll_dice == 1:
        result = 'one'
    elif death_saving_throw_roll_dice == 20:
        result = 'twenty'
    elif death_saving_throw_roll_dice >= 10:
        result = 'passed'
    else:
        result = 'failed'

    return result

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
        weapon = weapons_collection.find_one({'name': weapons_list[0]})

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
        weapon1 = weapons_collection.find_one({'name': weapons_list[0]})
        weapon2 = weapons_collection.find_one({'name': weapons_list[1]})

        # Check if both weapons selected are two handed.
        if 'two_handed' in weapon1['properties'] and 'two_handed' in weapon2['properties']:
            raise PrepareWeaponException("You cannot equip two two-handed weapons.")
        elif 'two_handed' in weapon1['properties'] or 'two_handed' in weapon2['properties']:
            raise PrepareWeaponException("You cannot equip another weapon, if one is two-handed")
        else:
            prepared_weapons.append(weapon1['name'])
            prepared_weapons.append(weapon2['name'])

    return prepared_weapons
