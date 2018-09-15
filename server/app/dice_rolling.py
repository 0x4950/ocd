# Abilities for each skill
abilities_n_skills = {
  'strength': ("strength", "athletics"),
  'dexterity': ("dexterity", "acrobatics", "sleight_of_hand", "stealth"),
  'intelligence': ("intelligence", "arcana", "history", "history_stonework", "investigation", "nature", "religion"),
  'wisdom': ("wisdom", "animal_handling", "insight", "medicine", "perception", "survival"),
  'charisma': ("charisma", "deception", "intimidation", "performance", "persuasion")
}

def dice_rolling(character, player_ability_skill):
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
