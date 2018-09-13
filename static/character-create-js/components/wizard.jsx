import React, { Component } from 'react';

class Wizard extends Component{
  state = {
    materials: [
      "component_pouch",
      "arcane_focus"
    ],
    cantrips: [
      "light",
      "fire_bolt",
      "poison_spray",
      "ray_of_frost"
    ],
    main_weapons: [
      "quarterstaff",
      "dagger"
    ],
    packs: [
      "scholar_pack",
      "explorer_pack"   
    ],
    wizardSelected: {  
      material: 'component_pouch',
      cantrips: [],
      main_weapon: 'quarterstaff',
      pack: 'scholar_pack'
    }
  }

  componentDidMount() {
    this.props.handleClassAttrChange(this.state.wizardSelected);
  }

  render() {
    return (
      <React.Fragment>
        <select name='material' onChange={this.wizardChanged}>
          {this.state.materials.map(material => <option>{material.replace("_", " ")}</option>)}
        </select>
        <select name='cantrips' onChange={this.wizardChanged}>
          {this.state.cantrips.map(cantrip => <option>{cantrip.replace("_", " ")}</option>)}
        </select>
        <select name='main_weapon' onChange={this.wizardChanged}>
          {this.state.main_weapons.map(weapon => <option>{weapon.replace("_", " ")}</option>)}
        </select>
        <select name='pack' onChange={this.wizardChanged}>
          {this.state.packs.map(pack => <option>{pack.replace("_", " ")}</option>)}
        </select>
      </React.Fragment>
      );
  }

  wizardChanged = e => {
    const wizardSelected = {...this.state.wizardSelected};
    wizardSelected[e.target.name] = e.target.value;
    this.setState({ wizardSelected });
    this.props.handleClassAttrChange(wizardSelected);
  };
}

export default Wizard;