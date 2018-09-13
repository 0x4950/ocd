from . import views
import dice

db = views.db

combat_session_collection = db['combat_session_monsters']
spells_collection = db['spells']

# Cleric Life domain spells.
life_domain_spells = (('bless', 'cure_wounds'), (),
                      ('lesser_restoration', 'spiritual_weapon'), (),
                      ('beacon_of_hope', 'revivify'))

class PrepareSpellException(Exception):
    pass

def set_prepared_spells(character, selected_spells):
    level_legit = False
    prepared_spells = set()

    # Add again the domain spells, if any.
    if character['class'] == 'cleric':
        for level in range(character['level']):
            for domain_spell in life_domain_spells[level]:
                prepared_spells.add(domain_spell)

    if character['rest_status'] == 'rested':
        # Check if character can select all these spells.
        if character['prepared_spells_length'] >= len(selected_spells):
            for spell_name in selected_spells:
                # Load spell document from the database.
                spell_document = spells_collection.find_one({'name': spell_name})

                # Check if the spell level is alright.
                if character['level'] < 2 and spell_document['level'] <= 1:
                    level_legit = True
                elif character['level'] < 4 and spell_document['level'] <= 2:
                    level_legit = True
                elif character['level'] < 6 and spell_document['level'] <= 3:
                    level_legit = True
                else:
                    raise PrepareSpellException("Your level cannot choose that spell.")

                # Check if the character's class can choose that spell.
                if character['class'] in spell_document['class']:
                    class_legit = True
                else:
                    raise PrepareSpellException("Your class cannot choose that spell.")

                if level_legit and class_legit:
                    prepared_spells.add(spell_document['name'])
        else:
            raise PrepareSpellException("You cannot choose that many spells.")
    else:
        raise PrepareSpellException("You have to be rested in order to change your prepared spells list.")

    return prepared_spells

# Helper functions.
def saving_throw_roll_dice(character, ability, game_id):
    saving_throw_dice = 0
    has_advantage = False
    has_disavantage = False

    if ability in character['buffs']['saving_throws']['advantages']:
        saving_throw_advantage = True

    # Check if character has temporary buffs.
    for buff in character['buffs']['temporary']['saving_throws']:
        # Check if saving throw buffs cover the ability.
        if ability in buff['covers']:
            # Check the type of buff
            if buff['type'] == 'dice_roll_add':
                saving_throw_dice += dice.roll(buff['dice'])

                # Remove buff after it was used.
                if buff['expires_on_use']:
                    combat_session_collection.update_one(
                        {'game_id': ObjectId(game_id),
                         'character_documents.combatidentifier': character['combatidentifier']},
                        {'$pull': {'monsters.$.buffs.temporary.saving_throws': {'type': 'dice_roll_add'}}})
            elif buff['type'] == 'advantage':
                has_advantage = True

    roll_dice1 = dice.roll('1d20t')
    roll_dice2 = dice.roll('1d20t')

    # Check if character has lucky trait.
    if 'lucky' in character['buffs']['attack_rolls']:
        if roll_dice1 == 1:
            roll_dice1 = dice.roll('1d20t')

    if has_advantage and not has_disavantage:
        saving_throw_dice += max(roll_dice1, roll_dice2)
    elif has_disavantage and not has_advantage:
        saving_throw_dice += min(roll_dice1, roll_dice2)
    else:
        saving_throw_dice += roll_dice1

    # Add ability modifier
    saving_throw_dice += floor((character['ability_scores'][ability] - 10) / 2)

    return saving_throw_dice

def calculate_armor_class(character):
    # Get the normal armor class from characters document.
    armor_class = character['armor_class']

    # Check if the target has equipped shield.
    if 'equipped' in character:
        if 'shield' in character['equipped']:
            armor_class += 2

    # Check if there are any temporary buffs affecting character's armor class.
    if 'buffs' in character:
        if 'temporary' in character['buffs']:
            if 'armor_class' in character['buffs']['temporary']:
                for buff in character['buffs']['temporary']['armor_class']:
                    if buff['type'] == 'flat':
                        armor_class += buff['amount']
                    if buff['type'] == 'replacement':
                        armor_class = buff['amount']

    return armor_class

def spell_attack_roll(actor, target, range_type):
    spell_attack_roll_status = None
    has_disadvantage = False
    has_advantage = False
    spell_attack_roll_result = 0  # Variable for the final returning result.

    # For ranged spell attack rolls.
    if range_type == 'ranged':
        # Calculate the distance between the characters.
        character_distance = euclidean_distance(actor['position'], target['position'])

        # If their distance is within reach(5 ft.) the actor gets disadvantage.
        if character_distance == 5:
            has_disadvantage = True

    # Roll the dice
    spell_attack_roll_dice1 = dice.roll('1d20t')
    spell_attack_roll_dice2 = dice.roll('1d20t')

    # Depending on advantages/disadvantages use the correct dice roll.
    if has_disadvantage and not has_advantage:
        spell_attack_roll_result = min(spell_attack_roll_dice1, spell_attack_roll_dice2)
    elif has_advantage and not has_disadvantage:
        spell_attack_roll_result = min(spell_attack_roll_dice1, spell_attack_roll_dice2)
    else:
        spell_attack_roll_result = spell_attack_roll_dice1

    if spell_attack_roll_result == 1:
        # Rolling 1
        spell_attack_roll_status = 'miss'
    elif spell_attack_roll_result == 20:
        # Rolling 20
        spell_attack_roll_status = 'critical'
    else:
        # Spellcasting ability modifier
        spell_attack_roll_result += floor((actor['ability_scores'][actor['spellcasting_ability']] - 10) / 2)

        # Proficiency Bonus.
        spell_attack_roll_result += actor['proficiency_bonus']

        # Calculate target's armor class
        target_armor_class = calculate_armor_class(target)

        if spell_attack_roll_result >= target_armor_class:
            spell_attack_roll_status = 'success'
        else:
            spell_attack_roll_status = 'miss'

    return spell_attack_roll_status

def apply_healing(game_id, actor, target, calc_amount, max_amount):
    healing_amount = 0

    # Check if target has the maximum healing buff.
    if 'maximum_healing' in target['buffs']['temporary']['healing']:
        healing_amount = max_amount
    else:
        healing_amount = calc_amount

    # Check if actor has any buff.
    if 'discipline_of_life' in actor['buffs']['spellcasting']:
        healing_amount += 2 + 2

    # See if target has maximum hit points buff.
    if 'maximum_hit_points' in target['buffs']['temporary']:
        for buff in target['buffs']['temporary']['maximum_hit_points']:
            # Increase maximum hit points of the character by the buff amount.
            target['maximum_hit_points'] += buff['amount']

    # Healing amount must not exceed target's maximum hit points.
    if (healing_amount + target['current_hit_points']) > target['maximum_hit_points']:
        healing_amount = target['maximum_hit_points'] - target['current_hit_points']

    # Update target's document with new current_hit_points.
    combat_session_collection.update_one(
        {'game_id': ObjectId(game_id), 'character_documents.combat_identifier': target['combat_identifier']},
        {'$inc': {'character_documents.$.current_hit_points': healing_amount}})

    return healing_amount

# Check if there is a slot available for a spell.
def check_slot_availability(actor, spell):
    # Initialize slot as unavailable.
    slot_available = False

    # For every slot level between the spell's level slot and the maximum slot level available.
    for slot_level in range(spell['level'], 4):
        # Check if the the slots already used do not surpass the available spell slots.
        if actor['spell_slots_used'][slot_level - 1] < actor['spell_slots'][slot_level - 1]:
            slot_available = True

    return slot_available

def check_duplicate_buff(target, buff_type, buff_name):
    result = True

    if target['buffs']['temporary'][buff_type]:
        for existing_buff in target['buffs']['temporary'][buff_type]:
            if existing_buff['name'] == buff_name:
                result = False
                break

    return result

### Class Abilities ###
def channel_divinity(actor, game_id, time, targets, subspell):
    if subspell == 'turn_undead':
        channel_divinitiy_turn_undead(actor, game_id, time)
    elif subspell == 'preserve_life':
         return channel_divinitiy_preserve_life(actor, targets, game_id)

def channel_divinitiy_turn_undead(actor, game_id, time):
    reply_msg = {}

    # Get actors position.
    character_xy = divmod(actor['position'], 8)

    # Turn feet into grid squares.
    grid_squares = 30 / 5

    # Find the four corners which set the perimeter for the range.
    lowest_i = character_xy[0] - grid_squares
    highest_i = character_xy[0] + grid_squares
    lowest_y = character_xy[1] - grid_squares
    highest_y = character_xy[1] + grid_squares

    # Check for every character in the battlefield
    monsters = combat_session_collection.find_one(
        {'game_id': ObjectId(game_id), 'character_documents.type': 'monster'},
        {'_id': 0, 'character_documents': 1})['character_documents']

    for monster in monsters:
        if monster['type'] == 'monster' and monster['monster_type'] == 'undead':
            # Get monster's coordinates.
            monster_xy = divmod(monster['position'], 8)

            if monster_xy[0] >= lowest_i and monster_xy[0] <= highest_i and \
                monster_xy[1] >= lowest_y and monster_xy[1] <= highest_y:

                # The target rolls a Dexterity saving throw.
                target_rolled = saving_throw_roll_dice(monster, 'wisdom', game_id)

                # The actor calculates his spell save DC.
                spell_save_dc = 8 + actor['proficiency_bonus'] + \
                    floor((actor['ability_scores'][actor['spellcasting_ability']] - 10) / 2)

                if target_rolled <= spell_save_dc:
                    if 'channel_divinity_destroy_undead' in actor['buffs']['spellcasting']:
                        combat_session_collection.update_one(
                            {'game_id': ObjectId(game_id),
                            'character_documents.combat_identifier': monster['combat_identifier']},
                            {'$set': {'status': 'dead'}})
                    else:
                        temporary_buff = {}
                        temporary_buff['value'] = 'turned'
                        temporary_buff['expires'] = time + 60

                        combat_session_collection.update_one(
                            {'game_id': ObjectId(game_id),
                            'character_documents.combat_identifier': monster['combat_identifier']},
                            {'$addToSet': {'character_documents.$.debuffs.conditions': temporary_buff}})
                else:
                    reply_msg['msg'] = ". " + monster['combat_identifier'] + " succeed on a " + actor['spellcasting_ability'] + " saving throw and was not hit by the spell."

def channel_divinitiy_preserve_life(actor, targets, game_id):
    calc_heal = 5 * actor['level']
    return_msg = {}
    return_msg['healed_characters'] = []

    return_msg['type'] = 'healing'
    print(targets)
    # Divide those hit points among targets.
    calc_heal = (int)(calc_heal / len(targets))

    for target in targets:
        return_amount =  apply_healing(game_id, actor, target, calc_heal, calc_heal)

        healed_character = combat_session_collection.find_one(
            {'game_id': ObjectId(game_id),
             'character_documents.combat_identifier': target['combat_identifier']},
            {'_id': 0, 'character_documents.$': 1})['character_documents'][0]
        healed_character.pop('_id', None)
        healed_character['heal_amount'] = return_amount

        return_msg['healed_characters'].append(healed_character)

    return return_msg

def second_wind(actor, game_id, time):
    return_msg = {}
    return_msg['healed_characters'] = []

    return_msg['type'] = 'healing'

    # Calculate the amount of hit points.
    calc_heal = dice.roll('1d10t') + actor['level']
    max_heal = 10 + actor['level']

    return_amount = apply_healing(game_id, actor, actor, calc_heal, max_heal)

    healed_character = combat_session_collection.find_one(
        {'game_id': ObjectId(game_id),
         'character_documents.combat_identifier': actor['combat_identifier']},
        {'_id': 0, 'character_documents.$': 1})['character_documents'][0]
    healed_character.pop('_id', None)
    healed_character['heal_amount'] = return_amount

    return_msg['healed_characters'].append(healed_character)

    return return_msg

def action_surge(actor, game_id, time):
    # Increase the number of actions per turn.
    combat_session_collection.update_one(
        {'game_id': ObjectId(game_id), 'character_documents.combat_identifier': actor['combat_identifier']},
        {'$inc': {'character_documents.$.actions_per_turn': 1}})

### Spells ###

## Cleric ##

# Life domain spells
def bless(game_id, actor, targets, time):
    good_buff = True

    if len(targets) < 4:
        for target in targets:
            temporary_buff = {}
            temporary_buff['name'] = 'bless'
            temporary_buff['expires_on_use'] = False
            temporary_buff['type'] = 'dice_roll_add'
            temporary_buff['dice'] = '1d4t'
            temporary_buff['covers'] = ['stength', 'dexterity', 'constitution', 'wisdom', 'intelligence', 'charisma']
            temporary_buff['expires'] = time + 60

            for buff_type in ['attack_rolls', 'saving_throws']:
                if not check_duplicate_buff(target, buff_type, 'bless'):
                    good_buff = False
                    break

            if good_buff:
                combat_session_collection.update_one(
                    {'game_id': ObjectId(game_id), 'character_documents.combat_identifier': target['combat_identifier']},
                    {'$addToSet': {
                        'character_documents.$.buffs.temporary.saving_throws': temporary_buff,
                        'character_documents.$.buffs.temporary.attack_rolls': temporary_buff}})

    return None

def cure_wounds(game_id, actor, targets):
    target = targets[0]
    return_msg = {}
    return_msg['healed_characters'] = []

    return_msg['type'] = 'healing'

    calc_heal = dice.roll('1d8t')
    calc_heal += floor((actor['ability_scores'][actor['spellcasting_ability']] - 10) / 2)

    max_heal = 8 + floor((actor['ability_scores'][actor['spellcasting_ability']] - 10) / 2)

    return_amount = apply_healing(game_id, actor, target, calc_heal, max_heal)

    healed_character = combat_session_collection.find_one(
        {'game_id': ObjectId(game_id),
         'character_documents.combat_identifier': target['combat_identifier']},
        {'_id': 0, 'character_documents.$': 1})['character_documents'][0]
    healed_character.pop('_id', None)
    healed_character['heal_amount'] = return_amount

    return_msg['healed_characters'].append(healed_character)

    return return_msg

def lesser_restoration(game_id, actor, targets):
    target = targets[0]
    conds = ['blinded', 'deafened', 'paralyzed', 'poisoned']
    
    for condition in conds:
        if condition in target['conditions']:
            combat_session_collection.update_one(
                {'game_id': ObjectId(game_id),
                 'character_documents.combat_identifier': target['combat_identifier']},
                {'$pull': {'character_documents.$.conditions': condition}})

def spiritual_weapon(game_id, actor, targets):
    target = targets[0]
    damage_type = 'force'
    reply_msg = {}

    actor_roll = spell_attack_roll(actor, target, 'melee')

    if actor_roll == 'critical':
        damage_done = dice.roll('2d8t')
        damage_done += floor((actor['ability_scores'][actor['spellcasting_ability']] - 10) / 2)
    elif actor_roll == 'success':
        damage_done = dice.roll('2d8t')
        damage_done += floor((actor['ability_scores'][actor['spellcasting_ability']] - 10) / 2)

    if actor_roll == 'miss':
        reply_msg['msg'] = ". " + actor['combat_identifier'] + " failed on a melee spell attack against " + target['combat_identifier']
    else:
        reply_msg = apply_damage(damage_done, ObjectId(game_id), target, damage_type)
    return reply_msg

def beacon_of_hope(game_id, actor, targets, time):
    for target in targets:
        good_buff = True

        temporary_buff = {}
        temporary_buff['name'] = 'bacon_of_hope'
        temporary_buff['expires_on_use'] = False
        temporary_buff['type'] = 'advantage'
        temporary_buff['covers'] = ['wisdom']
        temporary_buff['expires'] = time + 60

        for buff_type in ['death_saving_throws', 'saving_throws']:
            if not check_duplicate_buff(target, buff_type, 'beacon_of_hope'):
                good_buff = False
                break

        if good_buff:
            combat_session_collection.update_one(
            {'game_id': ObjectId(game_id),
            'character_documents.combat_identifier': target['combat_identifier']},
            {'$addToSet': {'character_documents.$.buffs.temporary.saving_throws': temporary_buff,
                    'character_documents.$.buffs.temporary.death_saving_throws': temporary_buff,
                    'character_documents.$.buffs.temporary.healing': 'maximum_healing'}})

def revivify(game_id, actor, targets):
    target = targets[0]

    if target['health_status'] == 'dead':
        combat_session_collection.update_one(
            {'game_id': ObjectId(game_id),
             'character_documents.combat_identifier': target['combat_identiifer']},
            {'$set': {'character_documents.$.health_status': 'alive',
                      'character_documents.$.current_hit_points': 1}})

# Cantrips
def resistance(game_id, actor, targets, time):
    target = targets[0]
    temporary_buff = {}
    good_buff = True

    temporary_buff['name'] = 'resistance'
    temporary_buff['expires_on_use'] = True
    temporary_buff['type'] = 'dice_roll_add'
    temporary_buff['dice'] = '1d4t'
    temporary_buff['covers'] = ['stength', 'dexterity', 'constitution', 'wisdom', 'intelligence', 'charisma']
    temporary_buff['expires'] = time + 60

    for buff_type in ['saving_throws']:
        if not check_duplicate_buff(target, buff_type, 'resistance'):
            good_buff = False
            break

    if good_buff:
        combat_session_collection.update_one(
            {'game_id': ObjectId(game_id), 'character_documents.combat_identifier': target['combat_identifier']},
            {'$addToSet': {'character_documents.$.buffs.temporary.saving_throws': temporary_buff}})

def spare_the_dying(game_id, actor, targets):
    target = targets[0]

    if target['current_hit_points'] == 0:
        combat_session_collection.update_one({'game_id': ObjectId(game_id), 'character_documents.combat_identifier': target['combat_identifier']},
                                             {'$set': {'character_documents.$.health_status': 'stable'}})

def sacred_flame(game_id, actor, targets):
    target = targets[0]
    damage_done = 0
    damage_type = 'radiant'
    reply_msg = {}

    # The target rolls a Dexterity saving throw.
    target_rolled = saving_throw_roll_dice(target, 'dexterity', game_id)

    # The actor calculates his spell save DC.
    spell_save_dc = 8 + actor['proficiency_bonus'] + floor((actor['ability_scores'][actor['spellcasting_ability']] - 10) / 2)

    if target_rolled <= spell_save_dc:
        damage_done = dice.roll('1d8t')

        # Update monsters current hit points.
        apply_damage(damage_done, ObjectId(game_id), target, damage_type)

        # Update monsters current hit points.
        reply_msg = apply_damage(damage_done, ObjectId(game_id), target, damage_type)
    else:
        reply_msg['msg'] = ". " + target['combat_identifier'] + " succeed on a Dexterity saving throw and was not hit by the spell."

    return reply_msg

# 1st level spells
def guiding_bolt(game_id, actor, targets):
    target = targets[0]
    damage_done = 0
    damage_type = 'radiant'
    reply_msg = {}

    # Actor makes a ranged spell attack against the target.
    spell_status = spell_attack_roll(actor, target, 'ranged')

    if spell_status == 'success':
        damage_done = dice.roll('4d6t')

        # Update monsters current hit points.
        reply_msg = apply_damage(damage_done, ObjectId(game_id), target, damage_type)
    else:
        reply_msg['msg'] = ". " + actor['combat_identifier'] + " failed on a ranged spell attack against " + target['combat_identifier']

    return reply_msg

def healing_word(game_id, actor, targets):
    target = targets[0]
    return_msg = {}
    return_msg['healed_characters'] = []

    return_msg['type'] = 'healing'

    # Roll a dice for the amount of healing.
    calc_heal = dice.roll('1d4t')
    max_heal = 4

    return_amount = apply_healing(game_id, actor, target, calc_heal, max_heal)

    healed_character = combat_session_collection.find_one(
        {'game_id': ObjectId(game_id),
         'character_documents.combat_identifier': target['combat_identifier']},
        {'_id': 0, 'character_documents.$': 1})['character_documents'][0]
    healed_character.pop('_id', None)
    healed_character['heal_amount'] = return_amount

    return_msg['healed_characters'].append(healed_character)

    return return_msg

def inflict_wounds(game_id, actor, targets):
    target = targets[0]
    damage_done = 0
    damage_type = 'necrotic'
    reply_msg = {}

    # Actor makes a melee spell attack roll against the target.
    actor_roll = spell_attack_roll(actor, target, 'melee')

    if actor_roll == 'critical':
        damage_done = dice.roll('6d10t')
    elif actor_roll == 'success':
        damage_done = dice.roll('3d10t')

    if actor_roll == 'miss':
        reply_msg['msg'] = ". " + actor['combat_identifier'] + " failed on a melee spell attack against " + target['combat_identifier']
    else:
        # Update monsters current hit points.
        reply_msg = apply_damage(damage_done, ObjectId(game_id), target, damage_type)

    return reply_msg

def shield_of_faith(game_id, actor, targets, time):
    target = targets[0]
    good_buff = True

    temporary_buff = {}
    temporary_buff['expires_on_use'] = False
    temporary_buff['type'] = 'flat'
    temporary_buff['amount'] = 2
    temporary_buff['expires'] = time + 600

    for buff_type in ['armor_class']:
        if not check_duplicate_buff(target, buff_type, 'shield_of_faith'):
            good_buff = False
            break

    if good_buff:
        # Update character's temporary armor class buffs.
        combat_session_collection.update_one(
            {'game_id': ObjectId(game_id), 'character_documents.combat_identifier': target['combat_identifier']},
            {'$addToSet': {'character_documents.$.temporary.armor_class': temporary_buff}})

# 2nd level spells
def aid(game_id, actor, targets, time):
    temporary_buff = {}
    temporary_buff['name'] = 'aid'
    temporary_buff['expires_on_use'] = True
    temporary_buff['type'] = 'flat'
    temporary_buff['amount'] = 5
    temporary_buff['expires'] = time + 28800

    # Update character's temporary armor class buffs.
    for target in targets:
        good_buff = True

        for buff_type in ['current_hit_points', 'maximum_hit_points']:
            if not check_duplicate_buff(target, buff_type, 'aid'):
                good_buff = False
                break

        if good_buff:
            combat_session_collection.update_one(
                {'game_id': ObjectId(game_id), 'character_documents.combat_identifier': target['combat_identifier']},
                {'$addToSet': {'character_documents.$.buffs.temporary.current_hit_points': temporary_buff,
                               'character_documents.$.buffs.temporary.maximum_hit_points': temporary_buff}})

def hold_person(game_id, actor, targets, time):
    target = targets[0]
    temporary_buff = {}

    # The target rolls a Wisdom saving throw.
    target_rolled = saving_throw_roll_dice(target, 'wisdom', game_id)

    # The actor calculates his spell save DC.
    spell_save_dc = 8 + actor['proficiency_bonus'] + floor((actor['ability_scores'][actor['spellcasting_ability']] - 10) / 2)

    if target_rolled <= spell_save_dc:
        temporary_buff['value'] = 'paralyzed'
        temporary_buff['expires'] = time + 60

        combat_session_collection.update_one(
            {'game_id': ObjectId(game_id),
             'character_documents.combat_identifier': target['combat_identifier']},
            {'$addToSet': {'character_documents.$.debuffs.conditions': temporary_buff}})

def protection_from_poison(game_id, actor, targets):
    target = targets[0]

    if 'poisoned' in target['conditions']:
        combat_session_collection.update_one(
            {'game_id': ObjectId(game_id), 'character_documents.combat_identifier': target['combat_identifier']},
            {'$pull': {'character_documents.$.conditions': 'poisoned'}})

def mass_healing_word(game_id, actor, targets):
    return_msg = {}
    return_msg['healed_characters'] = []

    return_msg['type'] = 'healing'

    for target in targets:
        calc_heal = dice.roll('1d4t')
        max_heal = 4

        return_amount =apply_healing(game_id, actor, target, calc_heal, max_heal)

        healed_character = combat_session_collection.find_one(
            {'game_id': ObjectId(game_id),
             'character_documents.combat_identifier': target['combat_identifier']},
            {'_id': 0, 'character_documents.$': 1})['character_documents'][0]
        healed_character.pop('_id', None)
        healed_character['heal_amount'] = return_amount

        return_msg['healed_characters'].append(healed_character)

    return return_msg

def protection_from_energy(game_id, actor, targets, time, subspell):
    temporary_buff = {}

    temporary_buff['expires_on_use'] = False
    temporary_buff['expires'] = time + 3600
    
    spell_document = spells_collection.find_one({'name': spell_name})
    if subspell in spell_document['subspells']:
        temporary_buff['value'] = subspell

        # Update character's temporary armor class buffs.
        for target in targets:
            good_buff = True

            for buff_type in ['resistances']:
                if not check_duplicate_buff(target, buff_type, temporary_buff['value']):
                    good_buff = False
                    break

            if good_buff:
                combat_session_collection.update_one(
                    {'game_id': ObjectId(game_id), 'character_documents.combat_identifier': target['combat_identifier']},
                    {'$addToSet': {'character_documents.$.buffs.temporary.resistances': temporary_buff}})

## Wizard ##
# Cantrips #
def fire_bolt(game_id, actor, targets):
    damage_done = 0
    damage_type = 'fire'
    reply_msg = {}

    # Actor makes a ranged spell attack roll against the target.
    actor_roll = spell_attack_roll(actor, target[0], 'ranged')

    if actor_roll == 'critical':
        damage_done = dice.roll('2d10t')
    elif actor_roll == 'success':
        damage_done = dice.roll('1d10t')

    if actor_roll == 'miss':
        reply_msg['msg'] = ". " + actor['combat_identifier'] + " failed on a ranged spell attack against " + target['combat_identifier']
    else:
        # Update monsters current hit points.
        reply_msg = apply_damage(damage_done, ObjectId(game_id), target, damage_type)

    return reply_msg

def poison_spray(game_id, actor, targets):
    damage_done = 0
    damage_type = 'poison'
    reply_msg = {}

    # Load the character from the targets list.
    target = targets[0]

    # Roll a Constitution saving throw.
    target_roll = saving_throw_roll_dice(target, 'constitution', game_id)

    # The actor calculates his spell save DC.
    spell_save_dc = 8 + actor['proficiency_bonus'] + floor((actor['ability_scores'][actor['spellcasting_ability']] - 10) / 2)

    if target_roll < spell_save_dc:
        damage_done = dice.roll('1d12t')

        # Update monsters current hit points.
        reply_msg = apply_damage(damage_done, ObjectId(game_id), target, damage_type)
    else:
        reply_msg['msg'] = ". " + target['combat_identifier'] + " succeed on a Constitution saving throw and was not hit by the spell."

    return reply_msg

def ray_of_frost(game_id, actor, targets):
    damage_done = 0
    target = targets[0]
    damage_type = 'cold'
    reply_msg = {}

    actor_roll = spell_attack_roll(actor, target, 'ranged')


    if actor_roll == 'critical':
        damage_done = dice.roll('2d8t')
    elif actor_roll == 'success':
        damage_done = dice.roll('1d8t')

    if actor_roll == 'miss':
        reply_msg['msg'] = ". " + actor['combat_identifier'] + " failed on a ranged spell attack against " + target['combat_identifier']
    else:
        # Update monsters current hit points.
        reply_msg = apply_damage(damage_done, ObjectId(game_id), target, damage_type)

    return reply_msg

def shield(game_id, actor, time):
    total_alive_players = 0
    temporary_buff = {}
    good_buff = True

    # Calculate how many seconds is a round.
    result = combat_session_collection.find_one(
        {'game_id': ObjectId(game_id)})['character_documents']

    for character in result:
        if character['health_status'] == 'alive':
            total_alive_players += 1

    round_time = total_alive_players * 6
    temporary_buff['name'] = 'shield'
    temporary_buff['expires_on_use'] = False
    temporary_buff['type'] = 'flat'
    temporary_buff['amount'] = 5
    temporary_buff['expires'] = time + round_time

    for buff_type in ['armor_class']:
        if not check_duplicate_buff(target, buff_type, 'shield'):
            good_buff = False
            break

    if good_buff:
        # Update character's temporary armor class buffs.
        combat_session_collection.update_one(
            {'game_id': ObjectId(game_id),
            'character_documents.combat_identifier': actor['combat_identifier']},
            {'$addToSet': {'character_documents.$.buffs.temporary.armor_class': temporary_buff}})

def magic_missile(game_id, actor, targets):
    damage_done = 0
    damage_type = 'force'
    reply_msg = None

    for target in targets:
        damage_done = dice.roll('1d4t') + 1

        apply_damage(damage_done, ObjectId(game_id), target, damage_type)

        # Update monsters current hit points.
        reply_msg = apply_damage(damage_done, ObjectId(game_id), target, damage_type)

    return reply_msg


def false_life(game_id, actor, time):
    good_buff = True

    temporary_buff = {}
    temporary_buff['name'] = 'false_life'
    temporary_buff['expires_on_use'] = False
    temporary_buff['type'] = 'flat'
    temporary_buff['amount'] = dice.roll('1d4t')
    temporary_buff['expires'] = time + 3600

    for buff_type in ['temporary_hit_points']:
        if not check_duplicate_buff(target, buff_type, 'false_life'):
            good_buff = False
            break

    if good_buff:
        combat_session_collection.update_one(
            {'game_id': ObjectId(game_id),
            'character_documents.combat_identifier': target['combat_identifier']},
            {'$addToSet': {'character_documents.$.buffs.temporary.temporary_hit_points': temporary_buff}})

def mage_armor(game_id, actor, targets, time):
    target = targets[0]
    good_buff = True

    # Buff information.
    temporary_buff = {}
    temporary_buff['name'] = 'mage_armor'
    temporary_buff['expires_on_use'] = False
    temporary_buff['type'] = 'replacement'
    temporary_buff['amount'] = 13 + floor((target['ability_scores']['dexterity'] - 10) / 2)
    temporary_buff['expires'] = time + 28800

    if target['armor'] == None:
        for buff_type in ['armor_class']:
            if not check_duplicate_buff(target, buff_type, 'mage_armor'):
                good_buff = False
                break

        if good_buff:
            combat_session_collection.update_one(
                {'game_id': ObjectId(game_id),
                'character_documents.combat_identifier': target['combat_identifier']},
                {'$addToSet': {'character_documents.$.buffs.temporary.armor_class': temporary_buff}})

def acid_arrow(game_id, actor, targets):
    over_time_damage = False
    damage_done = 0
    damage_type = 'acid'
    end_turn_damage = 0
    target = targets[0]
    reply_msg = {}

    actor_roll = spell_attack_roll(actor, target, 'ranged')

    if actor_roll == 'critical':
        damage_done = dice.roll('8d4t')
        over_time_damage = True
    elif actor_roll == 'success':
        damage_done = dice.roll('4d4t')
        over_time_damage = True
    elif actor_roll == 'miss':
        damage_done = dice.roll('2d4t')
    
    if actor_roll == 'miss':
        reply_msg['msg'] = ". " + actor['combat_identifier'] + " failed on a ranged spell attack against " + target['combat_identifier']
    else: 
        reply_msg = apply_damage(damage_done, ObjectId(game_id), target, damage_type)

    if over_time_damage:
        # Buff information.
        temporary_buff = {}
        temporary_buff['expires_on_use'] = True
        temporary_buff['type'] = 'damage'
        temporary_buff['damage_type'] = 'acid'
        temporary_buff['amount'] = dice.roll('2d4t')

        combat_session_collection.update_one(
            {'game_id': ObjectId(game_id),
             'character_documents.combat_identifier': target['combat_identifier']},
            {'$addToSet': {'character_documents.$.debuffs.overtime_effects': temporary_buff}})

def scorching_ray(game_id, actor, targets):
    damage_done = 0
    damage_type = 'fire'

    # This spell can target at most 3 targets.
    if len(targets) < 4:
        available_rays = 3

        for target in targets:
            while available_rays > 0:
                # Initialize damage done for each target.
                damage_done = 0

                # Actor makes a ranged spell attack roll.
                actor_roll = spell_attack_roll(actor, target, 'ranged')

                if actor_roll == 'critical':
                    damage_done = dice.roll('4d6t')
                elif actor_roll == 'success':
                    damage_done = dice.roll('2d6t')

                apply_damage(damage_done, ObjectId(game_id), target, damage_type)
                
                available_rays -= 1
                
                if len(targets) == 3:
                    break
                elif (len(targets) == 2) and (available_rays == 1):
                    break

def vampiric_touch(game_id, actor, targets):
    damage_done = 0
    damage_type = 'necrotic'
    target = targets[0]
    reply_msg = {}

    actor_roll = spell_attack_roll(actor, target, 'melee')

    if actor_roll == 'critical':
        damage_done = dice.roll('6d6t')
    elif actor_roll == 'success':
        damage_done = dice.roll('3d6t')

    if actor_roll == 'miss':
        reply_msg['msg'] = ". " + actor['combat_identifier'] + " failed on a melee spell attack against " + target['combat_identifier']
    else:
        reply_msg = apply_damage(damage_done, ObjectId(game_id), target, damage_type)

    if damage_done != 0:
        # Calculate half the amount of necrotic damage dealt.
        calc_healing = damage_done / 2

        apply_healing(game_id, actors, target, calc_healing, calc_healing)
