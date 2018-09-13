from math import floor
from pymongo import MongoClient

client = MongoClient('mongodb://heroku_t67kkwpk:ucevqbvtnnv7lr2bl0sc33ov6d@ds011664.mlab.com:11664/heroku_t67kkwpk')
db = client.get_default_database()
packs_collection = db['packs']
armor_collection = db['armors']
weapons_collection = db['weapons']
spells_collection = db['spells']

MAX_ABILITY_SCORE = 20

def get_ability_score_modifier(obj, ability):
    return floor((obj.ability_scores[ability] - 10) / 2)

class CustomException(Exception):
    pass

# Proficiency bonus advantancement table.
proficiency_bonus_advantancement = (2, 2, 2, 2, 3)

# Cleric & Wizard spell slots table.
spell_slots_table = ((2, 0, 0), (3, 0, 0), (4, 2, 0), (4, 3, 0), (4, 3, 2))

# Cleric Life domain spells.
life_domain_spells = (('bless', 'cure_wounds'), (),
                      ('lesser_restoration', 'spiritual_weapon'), (),
                      ('beacon_of_hope', 'revivify'))

class Character:
    def __init__(self, **kwargs):
        # Attribute initialization.
        self.asi_used = False
        self.level_up_ready = False
        self.ability_score_points = 0
        self.ability_scores = {}
        self.buffs = {'attack_rolls': set(),
                      'armor_class': set(),
                      'damage_rolls': set(),
                      'spellcasting': set(),
                      'ability_checks': {
                          "advantages": set(),
                          "other": set()
                      },
                      'saving_throws': {
                          "advantages": set(),
                          "other": set(),
                      },
                      'resistances': set(), 'attacking': set(), 'sleep': set(), 'movement': set(),
                      'temporary': {
                          'saving_throws': set(),
                          'attack_rolls': set(),
                          'death_saving_throws': set(),
                          'healing': set(),
                          'current_hit_points': set(),
                          'maximum_hit_points': set(),
                          'resistances': set(),
                          'armor_class': set(),
                          'temporary_hit_points': set()
                      }}
        self.proficiencies = {'weapons': set(), 'tools': set(), 'armor': set(), 'skills': set(),
                              'saving_throws': set()}
        self.debuffs = {'ability_checks': {
                        "disadvantages": set()},
                        'spellcasting': set(),
                        'overtime_effects': set()}
        self.maximum_hit_points = 0
        self.armor_class = 0
        self.armor = set()
        self.weapons = list()
        self.equipment = []
        self.burned_spells_abilities = []
        self.current_hit_points = 0
        self.class_abilities = set()
        self.levels_gained = 0
        self.temporary_hit_points = 0
        self.conditions = set()
        self.equipped = list()

        # Set generic standard character information.
        self.game_id = kwargs['game_id']
        self.attack_points_per_turn = 2
        self.actions_per_turn = 1
        self.bonus_actions_per_turn = 1
        self.type = 'player_character'
        self.death_saving_throws_attempts = [0, 0]
        self.player_name = kwargs['player_name']
        self.name = kwargs['selected_name']
        self.rest_status = 'rested'
        self.health_status = 'alive'
        self.level = 1
        self.experience_points = 0
        self.proficiency_bonus = 2

        self.set_ability_scores(kwargs['selected_ability_scores'])

        # Set race related attributes.
        self.set_race_attributes(kwargs['selected_race'])
        self.set_ability_score_increase(kwargs['selected_race'])

        # Set class releated attributes.
        self.set_class_attributes(**kwargs)

        # Call generic functions that need class-specific checking.
        class_equipment = None
        if 'class_equipment' in kwargs['selected_class']['not_for_save']:
            class_equipment = kwargs['selected_class']['not_for_save']['class_equipment']
        
        self.set_skills(kwargs['selected_skills'], kwargs['selected_class']['not_for_save']['skills_pool'])
        self.set_equipment(kwargs['selected_equipment'], class_equipment, kwargs['selected_class'])
        self.set_armor(kwargs['selected_armor'], kwargs['selected_weapons'], kwargs['selected_class'])
        self.set_weapons(kwargs['selected_weapons'], kwargs['selected_armor'], kwargs['selected_class']['not_for_save']['equipment_pool'])
        self.set_hit_points()
        self.set_armor_class()

    # This method will set the ability scores.
    def set_ability_scores(self, ability_scores_chosen):
        for x in ability_scores_chosen:
            if ability_scores_chosen[x] in range(0, 21):
                self.ability_scores[x] = ability_scores_chosen[x]
            else:
                raise CustomException('Ability score not valid.')

    # This method will increase/decrease ability scores according to race.
    def set_ability_score_increase(self, race):
        for ability in race['not_for_save']['ability_score_increase']:
            self.ability_scores[ability] += race['not_for_save']['ability_score_increase'][ability]

    # This method will adds race related attributes.
    def set_race_attributes(self, race_attributes):
        for key in race_attributes:
            if key != 'not_for_save' and key != '_id':
                if hasattr(self, key):
                    if isinstance(race_attributes[key], dict):
                        for item in race_attributes[key]:
                            for subitem in race_attributes[key][item]:
                                if isinstance(race_attributes[key][item], dict):
                                    for x in race_attributes[key][item][subitem]:
                                        getattr(self, key)[item][subitem].add(x)
                                else:
                                    getattr(self, key)[item].add(subitem)
                    elif isinstance(getattr(self, key), set):
                        for item in kwargs['selected_class'][key]:
                            getattr(self, key).add(item)
                else:
                    setattr(self, key, race_attributes[key])

    def set_class_attributes(self, **kwargs):
        # For every field in the class dictionary.
        for key in kwargs['selected_class']:
            # If key is eligble to save.
            if key != 'funcs' and key != 'not_for_save' and key != '_id':    
                if hasattr(self, key):
                    if isinstance(kwargs['selected_class'][key], dict):
                        for item in kwargs['selected_class'][key]:
                            for subitem in kwargs['selected_class'][key][item]:
                                if isinstance(kwargs['selected_class'][key][item], dict):
                                    for x in kwargs['selected_class'][key][item][subitem]:
                                        getattr(self, key)[item][subitem].add(x)
                                else:
                                    getattr(self, key)[item].add(subitem)
                    elif isinstance(getattr(self, key), set):
                        for item in kwargs['selected_class'][key]:
                            getattr(self, key).add(item)
                else:
                    setattr(self, key, kwargs['selected_class'][key])

        if 'funcs' in kwargs['selected_class']['not_for_save']:
            for func in kwargs['selected_class']['not_for_save']['funcs']:
                if 'args' in func:
                    getattr(self, func['name'])(kwargs[func['args']])
                else:
                    getattr(self, func['name'])()

    # This method will set the skills
    def set_skills(self, skills_chosen, choosable_skills):
        if len(skills_chosen) < 3:
            for skill in skills_chosen:
                # Class-skill validation
                if skill in choosable_skills:
                    self.proficiencies['skills'].add(skill)
                else:
                    raise CustomException('You cannot choose ' + skill + ' as a skill.')
        else:
            raise CustomException("You can select up to 2 skills only.")

    def set_equipment(self, equipment_chosen, class_items, class_document):
        if equipment_chosen in class_document['not_for_save']['equipment_pool']['pack']:
            # Load pack's items from database
            equipment_chosen = packs_collection.find_one({"name": equipment_chosen})

            # Push an empty dictionary inside the equipment list
            self.equipment.append({})

            # Save the dictionary's index in order to push key-value pairs
            index = self.equipment.index({})

            for item in equipment_chosen:
                # Skip _id & name keys
                if item != 'name' and item != '_id':
                    # In the list there are non key-value elements
                    if isinstance(equipment_chosen[item], list):
                        for subitem in equipment_chosen[item]:
                            self.equipment.append(subitem)
                    else:
                        # Else it is a key-value pair
                        # and should be pushed in the dictionary inside the list
                        self.equipment[index][item] = int(equipment_chosen[item])
        else:
            raise CustomException('You cannot choose that pack.')

        # Add class related items.
        if class_items:
            for item in class_items:
                self.equipment.append(item)

    def set_cantrips_known(self):
        # Initialize class attribute.
        self.cantrips_known = 0

        if self.level < 4:
            self.cantrips_known = 3
        elif self.level < 10:
            self.cantrips_known = 4

    def set_cantrips(self, cantrips_chosen):
        self.cantrips = set()
        for i, cantrip in enumerate(cantrips_chosen):
            # Check if cantrips chosen do now exceed the cantrips known.
            if i < self.cantrips_known:
                # Check if spell is an eligable cantrip(exists, class-releated, zero level).
                if spells_collection.find_one({'name': cantrip, 'class': getattr(self, 'class'), 'level': 0}, {}):
                    self.cantrips.add(cantrip)
                else:
                    raise CustomException("You cannot choose that spell as a cantrip.")
            else:
                raise CustomException('You have chosen more cantrips than you need!')

    def set_hit_points(self):
        # Calculate the Constitution modifier.
        con_mod = get_ability_score_modifier(self, 'constitution')

        # Calculate 1st level hit points according to the class.
        self.maximum_hit_points = self.hit_points_1_level + con_mod

        # For each level beyond 1st add the standard number + current con_mod.
        if self.level > 1:
            for i in range(self.level-1):
                self.maximum_hit_points += self.hit_points_higher_levels + con_mod
        
        # Set the current hit points equal to the maximum hit points.
        self.current_hit_points = self.maximum_hit_points

    # This method will set the armor.
    def set_armor(self, armor_chosen, weapons_chosen, class_document):
        # If no proficiency
        # Add disadvantage to ability checks, saving throws, attack rolls
        # with Strength and Dexterity. No spellcasting.

        # Check for shield bound to weapon.
        for weapon in weapons_chosen:
            if 'shield' in weapons_chosen[weapon]:
                self.armor.add('shield')

        # Add shield if it is given by the class(e.g. Cleric).
        if 'class_armor' in class_document['not_for_save']:
            if 'shield' in class_document['not_for_save']['class_armor']:
                self.armor.add('shield')

        # Armor choosen.
        if 'armor' in class_document['not_for_save']['equipment_pool']:
            if armor_chosen in class_document['not_for_save']['equipment_pool']['armor']:
                for armor in armor_collection.find({}, {'_id': 0, 'name': 1}):
                    if armor['name'] in armor_chosen:
                        self.armor.add(armor['name'])
            else:
                raise CustomException('You cannot choose that armor.')

    def set_weapons(self, selected_weapons, selected_armor, character_equipment_pool):
        # Check for weapons bould to armor.
        for weapon in weapons_collection.find({}, {'_id': 0, 'name': 1}):
            if weapon['name'] in selected_armor:
                self.weapons.append(weapon['name'])

        # Check for the weapons selected.
        for weapon in selected_weapons:
            if weapon in character_equipment_pool:
                if selected_weapons[weapon] in character_equipment_pool[weapon]:
                    if '_if_proficient' in selected_weapons[weapon]:
                        pure_weapon = selected_weapons[weapon].split('_if_proficient')[0]
                        if pure_weapon in self.proficiencies['weapons']:
                            self.weapons.append(pure_weapon)
                        else:
                            raise CustomException('You do not have proficiency with that weapon.')
                    elif '_shield' in selected_weapons[weapon]:
                        pure_weapon = selected_weapons[weapon].split('_shield')[0]
                        self.weapons.append(pure_weapon)
                    elif 'two_' in selected_weapons[weapon]:
                        pure_weapon = selected_weapons[weapon].split('two_')[1]
                        
                        # Add the weapon two times.
                        self.weapons.append(pure_weapon)
                        self.weapons.append(pure_weapon)
                    else:
                        self.weapons.append(selected_weapons[weapon])
                else:
                    raise CustomException('You canot choose that weapon.')

    def set_spell_slots(self):
        self.spell_slots = spell_slots_table[self.level-1]
        self.spell_slots_used = [0, 0, 0, 0, 0, 0, 0, 0, 0]

    def set_prepared_spells_length(self):
        # Initialize class attribute.
        self.prepared_spells_length = 0

        temp = self.level + get_ability_score_modifier(self, self.spellcasting_ability)
        if temp > 0:
            self.prepared_spells_length = floor(temp)
        else:
            self.prepared_spells_length = 1

    def set_domain(self, domain_chosen):
        self.domain = domain_chosen

        if self.domain == 'life':
            # Bonus proficiency with heave armor.
            for armor in armor_collection.find({'armor_type': 'heavy_armor'}):
                self.proficiencies['armor'].add(armor['name'])
            
            # Disciple of Life buff
            self.buffs['spellcasting'].add('disciple_of_life')

            # Set domain featues for 1st level.
            self.life_domain_features()
        else:
            raise CustomException('You cannot select this Divine Domain.')
    
    def life_domain_features(self):
        # Initialize class attribute.
        self.prepared_spells = set()

        # Set 'channel_divinity_preserve life' class ability.
        if self.level > 1:
            self.class_abilities.add('preserve_life')

        # Set Life domain Spells, according to level.
        for level in range(self.level):
            for spell in life_domain_spells[level]:
                self.prepared_spells.add(spell)

    def set_armor_class(self):
        db_armor = None
        object_armor = None

        # Load armor from database self.armor
        for armor in self.armor:
            if armor != 'shield':
                object_armor = armor
        if object_armor:
            db_armor = armor_collection.find_one({"name": object_armor})

        # Calculate Dexterity modifier
        dex_mod = get_ability_score_modifier(self, 'dexterity')

        # If character wears an armor.
        if db_armor:
            # Check for Fighter 'Defense' trait.
            if 'defense' in self.buffs['armor_class']:
                self.armor_class += 1

            if db_armor['armor_type'] == 'medium_armor' and dex_mod > 2:
                dex_mod = 2

            # Heavy armor does does not the Dexterity modifier
            if db_armor['armor_type'] == 'heavy_armor':
                dex_mod = 0

            if db_armor['stealth_disadvantage'] is True:
                # Add disadvantage to stealth checks.
                self.debuffs['ability_checks']['disadvantages'].add('stealth')

            # Check if the Strength check required for the armor is passed.
            if self.ability_scores['strength'] < db_armor['str_requirement']:
                self.speed -= 10

            # Take the armor class and add the dexterity modifier.
            ac = db_armor['armor_class'] + dex_mod
            self.armor_class += ac
        else:
            self.armor_class += 10 + dex_mod

    def level_up(self, **kwargs):
        if self.level_up_ready:
            # Generic character advancements.
            self.level += self.levels_gained
            self.set_hit_points()
            self.proficiency_bonus = proficiency_bonus_advantancement[self.level-1]

            if getattr(self, 'class') == 'cleric':
                # Cleric stuff
                self.set_cantrips_known()
                self.set_prepared_spells_length()
                self.set_spell_slots()

                self.life_domain_features()

                if self.level >= 2:
                    self.class_abilities.add('channel_divinity')
                    self.class_abilities.add('turn_undead')
                if self.level >= 4 and self.asi_used is False:
                    self.ability_score_improvement(kwargs['new_ability_scores'])
                if self.level >= 5:
                    self.buffs['spellcasting'].add('destroy_undead')
            elif getattr(self, 'class') == 'fighter':
                # Fighter stuff
                if self.level >= 2:
                    self.class_abilities.add('action_surge')
                if self.level >= 3 and not getattr(self, 'martial_archetype'):
                    self.set_martial_archetype(kwargs['martial_archetype'])
                if self.level >= 4 and self.asi_used is False:
                    self.ability_score_improvement(kwargs['new_ability_scores'])
                if self.level >= 5:
                    self.set_extra_attack()
            elif getattr(self, 'class') == 'wizard':
                # Wizard stuff
                self.set_cantrips_known()
                self.set_prepared_spells_length()
                self.set_spell_slots()

                if self.level >= 2 and not getattr(self, 'arcane_tradition'):
                    self.set_arcane_tradition(kwargs['arcane_tradition'])
                if self.level >= 4 and self.asi_used is False:
                    self.ability_score_improvement(kwargs['new_ability_scores'])

        # Clean variables, so they cannot be used again.
        self.level_up_ready = False
        self.levels_gained = 0

    def ability_score_improvement(self, new_ability_scores):
        old_ability_scores_sum = 0
        new_ability_scores_sum = 0

        for ability in self.ability_scores:
            old_ability_scores_sum += self.ability_scores[ability]
        
        for ability in new_ability_scores:
            if int(new_ability_scores[ability]) in range(self.ability_scores[ability], 21):
                new_ability_scores_sum += int(new_ability_scores[ability])
            else:
                raise CustomException("Ability score is out of range.")

        if new_ability_scores_sum - old_ability_scores_sum <= self.ability_score_points:
            self.abilities_scores = new_ability_scores
            self.ability_score_points = 0
            self.asi_used = True
        elif new_ability_scores_sum - old_ability_scores_sum > self.ability_score_points:
            raise CustomException("You only have", self.ability_score_points, "points available.")

    def set_martial_archetype(self, selected_martial_archetype):
        if selected_martial_archetype == 'champion':
            self.martial_archetype = 'champion'
            self.buffs['attack_rolls'].add('improved_critical')

    def set_fighting_style(self, selected_fighting_style):
        if selected_fighting_style == 'archery':
            self.buffs['attack_rolls'].add('archery')
        elif selected_fighting_style == 'defense':
            self.buffs['armor_class'].add('defense')
        elif selected_fighting_style == 'dueling':
            self.buffs['damage_rolls'].add('dueling')
        elif selected_fighting_style == 'great_weapon_fighting':
            self.buffs['damage_rolls'].add('great_weapon_fighting')
        elif selected_fighting_style == 'two_weapon_fighting':
            self.buffs['damage_rolls'].add('two_weapon_fighting')
        else:
            raise CustomException("You cannot choose that fighting style.")

    def set_arcane_tradition(self, selected_arcane_tradition):
        if selected_arcane_tradition == 'school_of_evocation':
            self.arcane_tradition = 'school_of_evocation'
            self.buffs['spellcasting'].add('evocation_savant')
            self.buffs['spellcasting'].add('sculpt_spells')

    def set_extra_attack(self):
        # You can attack twice, instead of once, whenever you take the Attack action on your turn.
        self.attack_points_per_turn += 2
