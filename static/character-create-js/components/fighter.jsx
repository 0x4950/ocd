import React, { Component } from 'react';

class Fighter extends Component{
  state = {
    martial_archetypes: [
      "archery",
      "defense",
      "dueling",
      "two_weapon_fighting"
    ],
    armors:[
      "chain_mail",
      "leather_longbow"
    ],
    main_weapons:[
      "two_battleaxe",
      "two_flail",
      "two_glaive",
      "two_greataxe",
      "two_greatsword",
      "two_halberd",
      "two_lance",
      "two_longsword",
      "two_maul",
      "two_morningstar",
      "two_pike",
      "two_rapier",
      "two_scimitar",
      "two_shortsword",
      "two_trident",
      "two_war_pick",
      "two_warhammer",
      "two_whip",
      "battleaxe_shield",
      "flail_shield",
      "glaive_shield",
      "greataxe_shield",
      "greatsword_shield",
      "halberd_shield",
      "lance_shield",
      "longsword_shield",
      "maul_shield",
      "morningstar_shield",
      "pike_shield",
      "rapier_shield",
      "scimitar_shield",
      "shortsword_shield",
      "trident_shield",
      "war_pick_shield",
      "warhammer_shield",
      "whip_shield"
    ],
    secondary_weapons: [
      "light_crossbow",
      "two_handaxe"
    ],
    packs: [
      "dungeoneer_pack",
      "explorer_pack"
    ],
    fighterSelected: {  
      martial_archetype: 'archery',
      armor: 'chain_mail',
      main_weapon: 'two_battleaxe',
      secondary_weapon: 'light_crossbow',
      pack: 'dungeoneer_pack'
    }
  };

  componentDidMount() {
    this.props.handleClassAttrChange(this.state.fighterSelected);
  }

  render() {
    return (
      <React.Fragment>
        <select name='martial_archetype' onChange={this.fighterChanged}>
          {this.state.martial_archetypes.map(mar => <option>{mar.replace("_", " ")}</option>)}
        </select>
        <select name='armor' onChange={this.fighterChanged}>
          {this.state.armors.map(armor => <option>{armor.replace("_", " ")}</option>)}
        </select>
        <select name='main_weapon' onChange={this.fighterChanged}>
          {this.state.main_weapons.map(weapon => <option>{weapon.replace("_", " ")}</option>)}
        </select>
        <select name='secondary_weapon' onChange={this.fighterChanged}>
          {this.state.secondary_weapons.map(sec_weapon => <option>{sec_weapon.replace("_", " ")}</option>)}
        </select>
        <select name='pack' onChange={this.fighterChanged}>
          {this.state.packs.map(pack => <option>{pack.replace("_", " ")}</option>)}
        </select>
      </React.Fragment>
      );
  }

  fighterChanged = e => {
    const fighterSelected = {...this.state.fighterSelected};
    fighterSelected[e.target.name] = e.target.value;
    this.setState({ fighterSelected });
    this.props.handleClassAttrChange(fighterSelected);
  };
}

export default Fighter;