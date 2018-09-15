def roll_initiative(character_monster):
    seed()  # Random seed

    d20_result = randint(1, 20)

    proper_ability_modifier = floor((character_monster['ability_scores']['dexterity'] - 10) / 2)
    d20_result += proper_ability_modifier

    return d20_result