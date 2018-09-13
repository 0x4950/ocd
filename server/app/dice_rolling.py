# Abilities for each skill
abilities_n_skills = {
  'strength': ("strength", "athletics"),
  'dexterity': ("dexterity", "acrobatics", "sleight_of_hand", "stealth"),
  'intelligence': ("intelligence", "arcana", "history", "history_stonework", "investigation", "nature", "religion"),
  'wisdom': ("wisdom", "animal_handling", "insight", "medicine", "perception", "survival"),
  'charisma': ("charisma", "deception", "intimidation", "performance", "persuasion")
}

def dice_rolling(character, player_ability_skill):
  # Random seed
  seed()
  d20_result = 0
  player_skills = []
  player_document = None
  npc_document = None
  player_advantages = []
  player_disadvantages = []
  player_proficiency_bonus = 0
  player_ability_scores = {}
  has_advantage = False
  has_disadvantage = False

  # Load character document
  if characters_collection.find_one({'name': character}):
    player_document = characters_collection.find_one({'name': character})
    player_skills = player_document['proficiencies']['skills']
    player_proficiency_bonus = player_document['proficiency_bonus']
    player_ability_scores = player_document['ability_scores']

    player_advantages = player_document['buffs']['ability_checks']['advantages']
    player_disadvantages = player_document['debuffs']['ability_checks']['disadvantages']

  elif npcsCollection.find_one({'npc_name': character}):
    npc_document = npcsCollection.find_one({'npc_name': character})

    npc_document['skills'] = npc_document['ability_scores']

    if player_ability_skill in npc_document['skills']:
        d20_result += npc_document['skills'][player_ability_skill]

    player_ability_scores = npc_document['ability_scores'][0]

  for ability in abilities_n_skills:
      for skill in abilities_n_skills[ability]:
          # Get the correct ability modifier for the skill chosen
          if skill == player_ability_skill:
              proper_ability_modifier = floor((player_ability_scores[ability] - 10) / 2)
              d20_result += proper_ability_modifier

              # If ability is in advantage/disadvantage list add all their skills too
              if player_ability_skill in player_disadvantages:
                  has_disadvantage = True
              elif player_ability_skill in player_advantages:
                  has_advantage = True

  # Roll the dices
  d20_result1 = randint(1, 20)
  d20_result2 = randint(1, 20)

  # Check if character has lucky trait.
  if player_document:
      if 'lucky' in player_document['buffs']['ability_checks']['other']:
          if d20_result1 == 1:
              d20_result1 = randint(1, 20)


  # Check if character/npc has advantages/disadvantages.
  if has_disadvantage and not has_sadvantage:
      d20_result = min(d20_result1, d20_result2)
  elif has_advantage and not has_disadvantage:
      d20_result = max(d20_result1, d20_result2)
  else:
      d20_result = d20_result1

  # If player is proficient with this skill, add Proficiency Bonus
  if player_ability_skill in player_skills:
      if player_ability_skill == 'history_stonework':
          d20_result += player_proficiency_bonus * 2
      else:
          d20_result += player_proficiency_bonus

  return d20_result

  def check_actor_condition(character):
    has_bad_condition = False

    bad_conditions = ['paralyzed', 'turned']

    # Check for bad conditions.
    for condition in bad_conditions:
        if condition in character['conditions']:
            has_bad_condition = True

    # Check for temporary bad conditions.
    if 'conditions' in character['debuffs']:
        for temp_cond in character['debuffs']['conditions']:
            for condition in bad_conditions:
                if temp_cond['value'] == condition:
                    has_bad_condition = True

    return has_bad_condition

def gen_combat_id(name, number_id):
    # Lowercase the name and remove spaces.
    combat_identifier = name.lower().replace(" ", "_")

    # Add the unique number at the end of the string.
    combat_identifier += str(number_id)

    return combat_identifier

def roll_initiative(character_monster):
    seed()  # Random seed

    d20_result = randint(1, 20)

    proper_ability_modifier = floor((character_monster['ability_scores']['dexterity'] - 10) / 2)
    d20_result += proper_ability_modifier

    return d20_result


def turns_n_rounds(game_id, initiative_order):
    # Initialise the structures for handling turns and rounds and saves them to the database.
    combat_session_monsters_collection.update_one(
        {'game_id': game_id},
        {'$set': {'round': 1, 'turn': 0, 'round_length': len(initiative_order)}})


def euclidean_distance(old_position, new_position):
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


def belonger(game_id):
    """
    Check if player participates in the game with the 'game_id' provided.
    Return True if he participates, False if he does not.
    """
    if usersCollection.find_one(
            {'$and': [{'username': flask_login.current_user.id},
                      {'participatingGames': {'$in': [game_id]}}]}):
        return True
    return False

def apply_damage(amount, game_id, character, damage_type):
    """
    Applies the damage to the character or monster.
    Changes statuses of character/monster according to it's hit points.
    """
    new_status = None
    msg = {}
    db_update_object = {}

    msg["type"] = "apply_damage"

    # Check if target has resistance to that type of damage.
    if damage_type in character['buffs']['resistances']:
        amount /= 2
    elif 'resistances' in character['buffs']['temporary']:
        for buff in character['buffs']['temporary']['resistances']:
            if damage_type == buff['value']:
                amount /= 2

    # Check if character has temporary temporary hit points (No pun intended).
    if 'temporary_hit_points' in character['buffs']['temporary']:
        # For each temporary hit points buff.
        for buff in character['buffs']['temporary']['temporary_hit_points']:
            if buff['amount'] >= amount:
                # Temporary hit points can absorb all the damage amount.
                absorbed_amount = amount
            else:
                # All temporary hit points are spent but not all damage amount is covered.
                absorbed_amount = buff['amount']

            # Reduce the temporary hit points.
            combat_session_monsters_collection.update_one(
                {'game_id': game_id,
                 'character_documents.combat_identifier': character['combat_identifier']},
                {'$inc': {'character_documents.$.buffs.temporary.temporary_hit_points': -absorbed_amount}})

            # Reduce damage amount by absorbed amount.
            amount = amount - absorbed_amount

    # Check if character has temporary current hit points.
    if 'current_hit_points' in character['buffs']['temporary']:
        # For each current hit points buff.
        for buff in character['buffs']['temporary']['current_hit_points']:
            # Increase current hit points of the character by the buff amount.
            character['current_hit_points'] += buff['amount']

    # Calculate the character's current hit points, after substracting the damage.
    after_hit_points = character['current_hit_points'] - amount

    msg["damage_amount"] = amount

    # See if character has maximum hit points buff.
    if 'maximum_hit_points' in character['buffs']['temporary']:
        for buff in character['buffs']['temporary']['maximum_hit_points']:
            # Increase maximum hit points of the character by the buff amount.
            character['maximum_hit_points'] += buff['amount']

    # Characters can change heath status to 'unconscious', before 'dead'.
    if character['type'] == 'player_character':
        if after_hit_points <= -character['maximum_hit_points']:
            new_status = 'dead'
        elif after_hit_points <= 0:
            new_status = 'unconscious'
    elif character['type'] == 'monster':
        # Change displayed health status.
        percentage = after_hit_points / character['maximum_hit_points']
        
        if percentage <= 0:
            displayed_hp_status = 'Dead'
        elif percentage == 1:
            displayed_hp_status = 'Undamaged'
        elif percentage >= 0.75:
            displayed_hp_status = 'Minor wounded'
        elif percentage >= 0.50:
            displayed_hp_status = 'Wounded'
        elif percentage >= 0.25:
            displayed_hp_status = 'Heavily wounded'
        else:
            displayed_hp_status = 'Severely wounded'

        db_update_object['character_documents.$.displayed_hp_status'] = displayed_hp_status

        # Monsters get directly to 'dead' if they drop to zero hit points.
        if after_hit_points <= 0:
            new_status = 'dead'

            # Split monster's experience points to the characters.
            split_monster_exp(character, game_id)

    if new_status == 'dead':
        # Remove the dead player character from the initiative order list,
        # and decrease the round length by 1.
        combat_session_monsters_collection.update_one(
            {'game_id': game_id},
            {'$pull': {'initiative_order': character['combat_identifier']},
             '$inc': {'round_length': -1}})

    db_update_object['character_documents.$.current_hit_points'] = after_hit_points

    if new_status == 'dead' or new_status == 'unconscious':
        db_update_object['character_documents.$.health_status'] = new_status

    # Update the current hit points and status of the character.
    updated_characters = combat_session_monsters_collection.find_one_and_update(
        {'game_id': game_id,
         'character_documents.combat_identifier': character['combat_identifier']},
        {'$set': db_update_object}, return_document=ReturnDocument.AFTER)['character_documents']

    for updated_character in updated_characters:
        if updated_character['combat_identifier'] == character['combat_identifier']:
            msg['damaged_character'] = updated_character
            msg['damaged_character'].pop('_id', None)

    return msg

def check_experience_points(game_id, character_name):
    # Character advancement table.
    character_advancement_table = (300, 900, 2700, 6500)

    for i, value in enumerate(character_advancement_table):
        characters_collection.update_one(
            {'game_id': game_id,
             'name': character_name,
             'experience_points': {'$gte': value},
             'level': {'$lte': i+1}},
            {'$set': {'level_up_ready': True},
             '$inc': {'levels_gained': 1}})

        character_python_objects_collection.update_one(
            {'game_id': game_id,
             'name': character_name,
             'experience_points': {'$gte': value},
             'level': {'$lte': i+1}},
            {'$set': {'level_up_ready': True},
             '$inc': {'levels_gained': 1}})

        if i == 2:
            characters_collection.update_one(
                {'game_id': game_id,
                 'name': character_name,
                 'experience_points': {'$gte': value},
                 'asi_used': False},
                {'$inc': {'ability_score_points': 2}})

            character_python_objects_collection.update_one(
                {'game_id': game_id,
                 'name': character_name,
                 'experience_points': {'$gte': value},
                 'asi_used': False},
                {'$inc': {'ability_score_points': 2}})

def split_monster_exp(monster, game_id):
    character_counter = 0

    characters = combat_session_monsters_collection.find_one(
        {'game_id': game_id}, {'_id': 0, 'character_documents': 1})['character_documents']

    for character in characters:
        if (character['type'] == 'player_character') and (character['health_status'] == 'alive'):
            character_counter += 1

    exp_each = monster['experience'] / character_counter

    for character in characters:
        if (character['type'] == 'player_character') and (character['health_status'] == 'alive'):
            combat_session_monsters_collection.update_one(
                {'game_id': game_id,
                 'character_documents.combat_identifier': character['combat_identifier']},
                {'$inc': {'character_documents.$.experience_points': exp_each}})