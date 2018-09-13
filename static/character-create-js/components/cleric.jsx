import React, { Component } from 'react';

class Cleric extends Component{
  state = {
    divine_domains: [
      'life'
    ],
    cantrips: [
      'light',
      'resistance',
      'sacred_flame',
      'spare_the_dying',
    ],
    armors: [
      'scale_mail',
      'leather',
      'chain_mail_if_proficient'
    ],
    main_weapons: [
        'mace',
        'warhammer_if_proficient'
    ],
    secondary_weapons: [
        'club',
        'dagger',
        'greatclub',
        'handaxe',
        'javelin',
        'light_hammer',
        'mace',
        'quarterstaff',
        'sickle',
        'spear',
        'light_crossbow',
        'dart',
        'shortbow',
        'sling'
    ],
    packs: [
        'priest_pack',
        'explorer_pack'
    ],
    clericSelected: {  
      divine_domain: 'life',
      cantrips: [],
      armor: 'scale_mail',
      main_weapon: 'mace',
      secondary_weapon: 'club',
      pack: 'priest_pack'
    }
  }

  componentDidMount() {
    this.props.handleClassAttrChange(this.state.clericSelected);
  }

  render() {
    return (
      <React.Fragment>
        <select name='divine_domain' onChange={this.clericChanged}>
          {this.state.divine_domains.map(divineDomain => <option>{divineDomain.replace('_', ' ')}</option>)}
        </select>
        <select name='cantrips' onChange={this.clericChanged}>
          {this.state.cantrips.map(cantrip => <option>{cantrip.replace('_', ' ')}</option>)}
        </select>
        <span>{this.props.selectedRace === 'Dwarf' && 'I am a Dwarf and thus I have proficiency.'}</span>
        <select name='armor' onChange={this.clericChanged}>
          {this.state.armors.map(armor => <option>{armor.replace('_', ' ')}</option>)}
        </select>
        <select name='main_weapon' onChange={this.clericChanged}>
          {this.state.main_weapons.map(mainWeapon => <option>{mainWeapon.replace('_', ' ')}</option>)}
        </select>
        <select name='secondary_weapon' onChange={this.clericChanged}>
          {this.state.secondary_weapons.map(secondaryWeapon => <option>{secondaryWeapon.replace('_', ' ')}</option>)}
        </select>
        <select name='pack' onChange={this.clericChanged}>
          {this.state.packs.map(pack => <option>{pack.replace('_', ' ')}</option>)}
        </select>
      </React.Fragment>
      );
  }

  clericChanged = e => {
    const clericSelected = {...this.state.clericSelected};
    clericSelected[e.target.name] = e.target.value;
    this.setState({ clericSelected });
    this.props.handleClassAttrChange(clericSelected);
  };
}

export default Cleric;