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

  return has_bad_condition1