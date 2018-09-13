import React, { Component } from 'react';

class Skills extends Component {
  state = {
    skills: {
      Fighter: [
        'Acrobatics',
        'Animal Handling',
        'Athletics',
        'History',
        'Insight',
        'Intimidation',
        'Perception',
        'Survival'
      ],
      Wizard: [
        'Arcana',
        'History',
        'Insight',
        'Investigation',
        'Medicine',
        'Religion'
      ],
      Cleric: [
        'History',
        'Insight',
        'Medicine',
        'Persuasion',
        'Religion'
      ]
    },
  }

  render() {
    return (
      <React.Fragment>
        {this.state.skills[this.props.selectedClass].map(skill => <div><input value={skill} type="checkbox"/>{skill}</div>)}
      </React.Fragment>
    );
  }
}

export default Skills;