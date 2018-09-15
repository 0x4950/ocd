from app import mongo, character

classesCollection = mongo.db.classes
racesCollection = mongo.db.races

skills = ('acrobatics', 'animal_handling', 'arcana', 'athletics', 'deception', 'history',
          'insight', 'intimidation', 'investigation', 'medicine', 'nature', 'perception',
          'performance', 'persuasion', 'sleight_of_hand', 'religion', 'stealth', 'survival')

def creator(form, player_name, game_id):
    selected_ability_scores = dict()
    selected_skills = set()
    char_creation_args = dict()

    # Pass form information as arguments to create a Character object.
    char_creation_args['game_id'] = game_id
    char_creation_args['player_name'] = player_name
    char_creation_args['selected_name'] = form.characterName.data
    char_creation_args['selected_race'] = racesCollection.find_one({'race': form.race.data})
    char_creation_args['selected_class'] =  classesCollection.find_one({'class': form.dclass.data})
    char_creation_args['selected_level'] = form.level.data
    char_creation_args['selected_alignment'] = form.alignment.data
    char_creation_args['selected_cantrips'] = form.cantrips.data
    char_creation_args['selected_armor'] = form.armor.data
    char_creation_args['selected_equipment'] = form.pack.data
    char_creation_args['selected_weapons'] = {'main_weapon': form.main_weapon.data,
                                              'secondary_weapon': form.secondary_weapon.data}

    # Save each ability score into a dictionary, and pass the dictionary.
    selected_ability_scores['strength'] = form.strength.data
    selected_ability_scores['dexterity'] = form.dexterity.data
    selected_ability_scores['constitution'] = form.constitution.data
    selected_ability_scores['intelligence'] = form.intelligence.data
    selected_ability_scores['wisdom'] = form.wisdom.data
    selected_ability_scores['charisma'] = form.charisma.data

    char_creation_args['selected_ability_scores'] = selected_ability_scores

    # Find and pass only the checked skills.
    for skill in skills:
        if getattr(form, skill).data is True:
            selected_skills.add(skill)
    char_creation_args['selected_skills'] = selected_skills

    # Each has has unique selectable attributes that are needed.
    selected_class = form.dclass.data
    if selected_class == 'cleric':
        char_creation_args['selected_domain'] = form.divine_domain.data
    elif selected_class == 'fighter':
        char_creation_args['selected_fighting_style'] = form.fighting_style.data
    elif selected_class == 'wizard':
        char_creation_args['selected_material'] = form.material.data

    # Create the Character object.
    character_object = Character(**char_creation_args)

    return character_object
