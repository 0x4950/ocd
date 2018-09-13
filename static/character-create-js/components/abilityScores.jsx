import React, { Component } from 'react';

class AbilityScores extends Component {
  state = {
    abilityScores: [
      'Strength',
      'Dexterity',
      'Constitution',
      'Wisdom',
      'Charisma',
      'Intelligence'
    ]
  }
  render() {
    return (
      <React.Fragment>
        {this.state.abilityScores.map(abilityScore => <div><input type="number" placeholder={abilityScore} /></div>)}
      </React.Fragment>
    );
  }
}

export default AbilityScores;