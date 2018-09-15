@socketio.on('action', namespace='/combat_page_namespace')
def character_monster_action(data):
    targets = []
    attack_range_permitted = True
    critical = False
    update_action = True
    rdy_to_attack = False
    bad_condition = True
    rdy_to_cast_spell = False
    rdy_to_use_ability = False
    this_spell_is_cantrip = False
    previous_casted_spell_is_cantip = False
    weapon_property = None
    valid_health_points = True
    invalid_attack_points = False
    weapon_is_melee_light =  False
    different_weapon = False
    bonus_action_attack = False
    weapon_uniqueness_counter = 0
    actor_melee_light_weapon_used = False
    db_search_object = {}
    db_update_object = {}
    spell = None
    subability = None
    self_casted = False
    chars_distance = 9000
    allowed_distance = 0
    msg = {}
    broadcast_value = False

    # Retrieve combat document from the database.
    combat_document = combat_session_monsters_collection.find_one({'game_id': ObjectId(session['game_id'])})
    combat_characters = combat_document['character_documents']

    # Check if targets and actor is either a monster or a character.
    for character in combat_characters:
        if character['combat_identifier'] == data['actor']:
            actor = character
        if 'targets' in data:
            for target in data['targets']:
                if character['combat_identifier'] == target:
                    targets.append(character)

    # Retrieve weapon/spell information from the database.
    if 'weapon' in data:
        weapon = weapons_collection.find_one({'name': data['weapon']})

        # Check if the weapon is used with a certain property(e.g. melee/thrown)
        if 'weapon_property' in data:
            weapon_property = data['weapon_property']
        
        # Check if the weapon is melee and has the 'light' property.
        if 'light' in weapon['properties'] and weapon['attack_range'] == 'melee':
            weapon_is_melee_light = True

        # Check if weapon is different from the one used in character's action.
        for w in actor['weapons']:
            if w == data['weapon']:
                weapon_uniqueness_counter += 1
        if weapon_uniqueness_counter > 1 or data['weapon'] != actor['weapon_used']:
            different_weapon = True

        # Check if the actor is trying to attack with a weapon he is not supposed to.
        if (actor['attack_points'] - weapon['attack_points']) == 1:
            invalid_attack_points = True
        elif actor['attack_points'] < actor['attack_points_per_turn']:
            invalid_attack_points = True

        # Check if light weapon has already been used.
        if actor['weapon_used']:
            if weapons_collection.find_one(
                    {'name': actor['weapon_used'],
                     'attack_range': 'melee', 'properties': {'$in': ['light']}}):
                actor_melee_light_weapon_used = True

        # Set the distance allowed by the weapon.
        if (weapon['attack_range'] == 'melee' and not weapon_property) or weapon_property == 'melee' or weapon_property == 'versatile':
            allowed_distance = 5
        elif (weapon['attack_range'] == 'melee' and weapon_property == 'thrown') or weapon['attack_range'] == 'ranged':
            allowed_distance = weapon['long_range']
    elif 'spell' in data:
        spell = spells_collection.find_one({'name': data['spell']})

        # Get the subspell.
        if 'subspell' in data:
            subspell = data['subspell']

        # Save the spell distance.
        allowed_distance = spell['range']

        # Check for slot availability.
        available_slot = spells.check_slot_availability(actor, spell)

        # Check if the spell is a cantrip.
        if spell['level'] == 0:
            this_spell_is_cantrip = True

        # Check if previous spell used was cantrip.
        if actor['previous_casted_spell']:
            if spells_collection.find_one({'name': actor['previous_casted_spell'], 'level': 0}):
                previous_casted_spell_is_cantip = True
    elif 'ability' in data:
        ability = abilities_collection.find_one({'name': data['ability']})

        # Get the sub-ability.
        if 'sub_ability' in data:
            subability = abilities_collection.find_one({'name': data['sub_ability']})

        # Get the ability/subability distance.
        if subability:
            if subability['target'] == 'self_cast':
                self_casted = True
            else:
                allowed_distance = subability['range']
        else:
            if ability['target'] == 'self_cast':
                self_casted = True
            else:
                allowed_distance = ability['range']

    # Check if actor and targets have valid health statuses.
    if 'targets' in data:
        if actor['health_status'] == 'dead' or actor['health_status'] == 'unconscious':
            valid_health_points = False

        for target in targets:
            if target['health_status'] == 'dead':
                valid_health_points = False

    # Calculate the distance between the actor & the targets.
    if targets and actor:
        for target in targets:
            chars_distance = euclidean_distance(actor['position'], target['position'])

            # Check if the distance criterion is met.
            if (chars_distance > allowed_distance) or self_casted:
                attack_range_permitted = False

    # Check for conditions that prevent character from using his action.
    bad_condition = check_actor_condition(actor)

    if not bad_condition:
        if attack_range_permitted:
            if data['action'] == 'attack' or data['action'] == 'two_weapon_fighting':
                if valid_health_points:
                    if data['action_type'] == 'action' and actor['actions_used'] < actor['actions_per_turn']:
                        if not invalid_attack_points:
                            rdy_to_attack = True
                        else:
                            msg['msg'] = "You cannot make another attack on the same turn."
                    elif data['action_type'] == 'bonus_action' and actor['bonus_actions_used'] < actor['bonus_actions_per_turn']:
                        # Check if the weapons used in both attacks are light.
                        if actor_melee_light_weapon_used and weapon_is_melee_light:
                            # Check if weapons are different.
                            if different_weapon:
                                rdy_to_attack = True
                                bonus_action_attack = True
                            else:
                                msg['msg'] = "You cannot attack with the same weapon."
                        else:
                            msg['msg'] = "You have to use melee light weapons with both actions"
                    else:
                        msg['msg'] = "You have already used your action/bonus action for this turn"
                else:
                    msg['msg'] = "Both characters and monsters must be alive in order for that action."
            elif data['action'] == 'spell_cast' or data['action'] == 'bonus_action_spell_cast':
                if valid_health_points:
                    if data['action_type'] == 'action' and spell['action_use'] == 'action' \
                        and actor['actions_used'] < actor['actions_per_turn']:
                        if (not actor['previous_casted_spell']) or this_spell_is_cantrip:
                            if available_slot:
                                if spell['name'] not in actor['burned_spells_abilities']:
                                    rdy_to_cast_spell = True
                                else:
                                    msg['msg'] = "You must finish a short/long rest before using that spell again."
                            else:
                                msg['msg'] = "You do not have any more slots for a spell of this level."
                        else:
                            msg['msg'] = "You cannot perform that action."
                    elif data['action_type'] == 'bonus_action' and spell['action_use'] == 'bonus_action' \
                        and actor['bonus_actions_used'] < actor['bonus_actions_per_turn']:
                        if (not actor['previous_casted_spell']) or previous_casted_spell_is_cantip:
                            if available_slot:
                                if spell['name'] not in actor['burned_spells_abilities']:
                                    rdy_to_cast_spell = True
                                else:
                                    msg['msg'] = "You must finish a short/long rest before using that spell again."
                            else:
                                msg['msg'] = "You do not have any more slots for a spell of this level."
                        else:
                            msg['msg'] = "You cannot perform that action."
                    else:
                        msg['msg'] = "You have already used your action/bonus action for this turn."
                else:
                    msg['msg'] = "Both characters and monsters must be alive in order for that action."
            elif data['action'] == 'use_ability':
                # Check if the actor has used all his actions, or one is not needed.
                if (data['action_type'] == 'action' and actor['actions_used'] < actor['actions_per_turn']) or \
                    ability['action_used'] == 'no_action':
                    # Check if the ability is has been used again.
                    if ability['name'] not in actor['burned_spells_abilities']:
                        rdy_to_use_ability = True
                    else:
                        msg['msg'] = "You must finish a short/long rest before using that spell again."
                else:
                    msg['msg'] = "You have already used your action/bonus action for this turn."
        else:
            msg['msg'] = "Target is out of range."
    else:
        msg['msg'] = "Your current condition does not allow you to use an action this turn."

    # Handle death saving throws for unconscious characters.
    if data['action'] == 'death_saving_throw':
        db_update_object = {}

        if data['action_type'] == 'action' and actor['actions_used'] < actor['actions_per_turn']:
            if actor['health_status'] == 'unconscious':
                # Death Saving Throw.
                death_saving_throw = attacks.death_saving_throw(actor)

                if death_saving_throw == 'passed':
                    actor['death_saving_throws_attempts'][0] += 1
                    msg["msg"] = "You have passed this round's death saving throw roll."
                elif death_saving_throw == 'failed':
                    actor['death_saving_throws_attempts'][1] += 1
                    msg["msg"] = "You have failed this round's death saving throw roll."
                elif death_saving_throw == 'one':
                    actor['death_saving_throws_attempts'][1] += 2
                    msg["msg"] = "You have rolled 1 this round's death saving throw roll."

                db_update_object['character_documents.$.death_saving_throws_attempts'] = actor['death_saving_throws_attempts']

                # Check if actor's status is changing.
                if death_saving_throw == 'twenty' or actor['death_saving_throws_attempts'][0] >= 3:
                    if death_saving_throw == 'twenty':
                        msg["msg"] = "You have rolled 20 on this round's death saving throw."
        
                    msg["msg"] += " Your character is now stable, but unconscious."
                    msg["type"] = "alive_by_attempts"

                    actor['health_status'] = 'stable'
                    db_update_object['character_documents.$.current_hit_points'] = 0
                elif actor['death_saving_throws_attempts'][1] >= 3:
                    msg["msg"] += " Your character is now dead."
                    msg['type'] = "dead_by_attempts"

                    actor['health_status'] = 'dead'

                if 'type' in msg:
                    if(msg['type'] == "alive_by_attempts") or (msg['type'] == "dead_by_attempts"):
                        # Remove the dead player character from the initiative order list,
                        # and decrease the round length by 1.
                        combat_session_monsters_collection.update_one(
                            {'game_id': ObjectId(session['game_id'])},
                            {'$pull': {'initiative_order': actor['combat_identifier']},
                                '$inc': {'round_length': -1}})

                db_update_object['character_documents.$.health_status'] = actor['health_status']

                combat_session_monsters_collection.update_one(
                    {'game_id': ObjectId(session['game_id']),
                     'character_documents.combat_identifier': actor['combat_identifier']},
                    {'$set': db_update_object,
                     '$inc': {'character_documents.$.actions_used': 1}})

                msg["msg"] += " Your current attempts are " + str(actor['death_saving_throws_attempts']) + "."
            else:
                msg['msg'] = "Character must be unconscious."
        else:
            msg['msg'] = "You have already used your action/bonus action for this turn."

    if data['action'] == 'don_shield' or data['action'] == 'doff_shield':
        if data['action_type'] == 'action' and actor['actions_used'] < actor['actions_per_turn']:
            if data['action'] == 'don_shield':
                try:
                    new_weapon_list = actor['equipped']
                    new_weapon_list.append('shield')

                    attack_weapon = attacks.set_prepared_weapons(actor, new_weapon_list)

                    combat_session_monsters_collection.update_one(
                        {'game_id': ObjectId(session['game_id']),
                        'character_documents.combat_identifier': actor['combat_identifier']},
                        {'$set': {'character_documents.$.equipped': attack_weapon}})
                    
                    msg['msg'] = "You have equipped the shield."
                except attacks.PrepareWeaponException as e:
                    error = e.args[0]
                    msg['msg'] = error
            elif data['action'] == 'doff_shield':
                if 'shield' in actor['equipped']:
                    # Remove the shield from character's equipped list.
                    combat_session_monsters_collection.update_one(
                        {'game_id': ObjectId(session['game_id']),
                        'character_documents.combat_identifier': actor['combat_identifier']},
                        {'$pull': {'character_documents.$.equipped': 'shield'}})
                    
                    msg['msg'] = "You no longer have a shield equipped."

            # Update actor's action/bonus action status.
            combat_session_monsters_collection.update_one(
                {'game_id': ObjectId(session['game_id']),
                    'character_documents.combat_identifier': actor['combat_identifier']},
                {'$inc': {'character_documents.$.actions_used': 1}})
        else:
            msg['msg'] = "You have already used your action/bonus action for this turn."

    if rdy_to_attack:
        broadcast_value = True
        # Attack roll.
        attack_status = attacks.attack_roll(actor, targets[0], weapon, weapon_property,
                                            chars_distance)
        # If actor hits the target.
        if attack_status == 'success' or attack_status == 'critical':
            # Damage roll variable
            if attack_status == 'critical':
                critical = True
                msg['msg'] = actor['name'] + " succeeded to critically hit " + target['name'] + " with his attack."
            else:
                msg['msg'] = actor['name'] + " succeeded to hit " + target['name'] + " with his attack."

            # Damage roll.
            damage_result = attacks.damage_roll(actor, targets[0], weapon, weapon_property,
                                                critical, bonus_action_attack)

            # Update monster's hit points.
            return_msg = apply_damage(damage_result, ObjectId(session['game_id']), targets[0],
                            weapon['damage_type'])
            
            # Merge two dictionaries.
            msg.update(return_msg)
        else:
            msg['msg'] = actor['name'] + " missed to hit " + target['name'] + " with his attack."

        # Check which action type to update.
        if data['action_type'] == 'action':
            update_obj = {'character_documents.$.actions_used': 1}
        elif data['action_type'] == 'bonus_action':
            update_obj = {'character_documents.$.bonus_actions_used': 1}

        # Update actor's action/bonus action status.
        combat_session_monsters_collection.update_one(
            {'game_id': ObjectId(session['game_id']),
            'character_documents.combat_identifier': actor['combat_identifier']},
            {'$inc': update_obj})

        if data['action_type'] == 'action':
            # Update actor's attack points.
            combat_session_monsters_collection.update_one(
                {'game_id': ObjectId(session['game_id']),
                'character_documents.combat_identifier': actor['combat_identifier']},
                {'$inc': {'character_documents.$.attack_points': -weapon['attack_points']}})

        # Update actor's weapon used.
        combat_session_monsters_collection.update_one(
            {'game_id': ObjectId(session['game_id']),
            'character_documents.combat_identifier': actor['combat_identifier']},
            {'$set': {'character_documents.$.weapon_used': weapon['name']}})
    elif rdy_to_cast_spell:
        if 'armor_proficiency_lack' not in actor['debuffs']['spellcasting']:
            params = [session['game_id'], actor]
            reply_msg = None

            # Check if spell is selfcasted. If not, send the targets as a parameter.
            if spell['range'] > 0:
                params.append(targets)

            # If the spell has a temporary aspect pass the time.
            if 'traits' in spell:
                if 'expires' in spell['traits']:
                    params.append(combat_document['time'])

            # If the spell has subspells, pass the one selected from the data.
            if 'subspells' in spell:
                params.append(subspell)

            targets_names = ""
            for target in targets:
                targets_names += target['combat_identifier']

                if target != targets[-1]:
                    targets_names += ", "

            msg['msg'] = actor['combat_identifier'] + " casted " + spell['name']

            if targets_names:
                msg['msg'] += " to " + targets_names

            if spell['type'] != 'utility' and spell['type'] != 'creation':
                reply_msg = getattr(spells, spell['name'])(*params)

            # Merge two dictionaries.
            if reply_msg:
                if 'msg' in reply_msg:
                    msg['msg'] += reply_msg['msg']
                else:
                    msg.update(reply_msg)
            
            # Broadcast spell cast.
            broadcast_value = True

            # Check which action type to update.
            if data['action_type'] == 'action':
                update_obj = {'character_documents.$.actions_used': 1}
            elif data['action_type'] == 'bonus_action':
                update_obj = {'character_documents.$.bonus_actions_used': 1}

            # Update actor's action/bonus action status.
            combat_session_monsters_collection.update_one(
                {'game_id': ObjectId(session['game_id']),
                 'character_documents.combat_identifier': actor['combat_identifier']},
                {'$inc': update_obj})

            # Update actor's spell casted.
            combat_session_monsters_collection.update_one(
                {'game_id': ObjectId(session['game_id']),
                 'character_documents.combat_identifier': actor['combat_identifier']},
                {'$set': {'character_documents.$.previous_casted_spell': spell['name']}})

            # List the spell as burned, if it needs short/long rest for re-use.
            if 'needs_rest' in spell:
                combat_session_monsters_collection.update_one(
                    {'game_id': ObjectId(session['game_id']),
                     'character_documents.combat_identifier': actor['combat_identifier']},
                    {'$addToSet': {'character_documents.$.burned_spells_abilities': spell['name']}})

            # Update actor's spell slots, only if spell is not a cantrip.
            if spell['level'] > 0:
                actor['spell_slots_used'][spell['level'] - 1] += 1
                combat_session_monsters_collection.update_one(
                    {'game_id': ObjectId(session['game_id']),
                    'character_documents.combat_identifier': actor['combat_identifier']},
                    {'$set': {'character_documents.$.spell_slots_used': actor['spell_slots_used']}})
        else:
            msg['msg'] = "You cannot cast a spell wearing armor that you lack proficiency with."
    elif rdy_to_use_ability:
        # Base parameters for every ability.
        params = [actor, session['game_id'], combat_document['time']]

        # Additional parameters for specific abilities.
        if subability:
            # Pass the targets.
            params.append(targets)

            # Pass the name of the sub-ability selected.
            params.append(subability['name'])

        # Call the function with the same name as the ability selected.
        reply_msg = getattr(spells, ability['name'])(*params)

        msg['msg'] = actor['combat_identifier'] + " is casting " + ability['name']
        if subability:
            targets_names = ""
            for target in targets:
                targets_names += target['combat_identifier']

                if target != targets[-1]:
                    targets_names += ", "
            
            msg['msg'] += " - " + subability['name'] + " to " + targets_names

        broadcast_value = True

        # Merge two dictionaries.
        if reply_msg:
            msg.update(reply_msg)

        # Check which action type to update.
        if ability['action_used'] == 'action':
            update_obj = {'character_documents.$.actions_used': 1}
        elif ability['action_used'] == 'bonus_action':
            update_obj = {'character_documents.$.bonus_actions_used': 1}
        elif ability['action_used'] == 'no_action':
            update_action = False

        # Update actor's action/bonus action status.
        if update_action:
            combat_session_monsters_collection.update_one(
                {'game_id': ObjectId(session['game_id']),
                 'character_documents.combat_identifier': actor['combat_identifier']},
                {'$inc': update_obj})

        # List the ability as burned, if it needs short/long rest for re-use.
        if 'rest' in ability:
            combat_session_monsters_collection.update_one(
                {'game_id': ObjectId(session['game_id']),
                 'character_documents.combat_identifier': actor['combat_identifier']},
                {'$addToSet': {'character_documents.$.burned_spells_abilities': ability['name']}})

    emit("message", msg, broadcast=broadcast_value, namespace='/combat_page_namespace')