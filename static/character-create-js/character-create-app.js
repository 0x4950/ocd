import React, { Component } from 'react';
import Fighter from './components/fighter';
import Cleric from './components/cleric';
import Wizard from './components/wizard';
import AbilityScores from './components/abilityScores';
import Skills from './components/skills';

class App extends Component {
  state = {
    alignments: [
      'Lawful Good',
      'Lawful Neutral',
      'Lawful Evil',
      'Neutral Good',
      'True Neutral',
      'Chaotic Good',
      'Chaotic Neutral',
      'Chaotic Evil'
    ],
    races: [
      'Human',
      'Dwarf',
      'Elf',
      'Halfling'
    ],
    classes: [
      'Fighter',
      'Wizard',
      'Cleric'
    ],
    selected: {
      class: 'Fighter',
      race: 'Human',
      alignment: 'Lawful Good'
    }
  }

  components = {
    Fighter: Fighter,
    Cleric: Cleric,
    Wizard: Wizard
  };

  render() {
    const CharacterClass = this.components[this.state.selected.class];

    return (
      <React.Fragment>
        <h1>Character Creation</h1>
        <input placeholder="Character name"></input>
        <select>
          {this.state.alignments.map(alignment => <option>{alignment}</option>)}
        </select>
        <select onChange={this.handleRaceChange}>
          {this.state.races.map(race => <option>{race}</option>)}
        </select>
        <span>Level: 1</span>
        <select onChange={this.handleClassChange}>
          {this.state.classes.map(charclass => <option>{charclass}</option>)}
        </select>
        <CharacterClass selectedRace={this.state.selected.race} handleClassAttrChange={this.handleClassAttrChange}/>
        <AbilityScores selectedRace={this.state.selected.class} />
        <Skills selectedClass={this.state.selected.class} />
      </React.Fragment>
    );
  }

  handleRaceChange = e => {
    const selected = {...this.state.selected};
    selected['race'] = e.target.value;
    this.setState({ selected });
  };

  handleClassChange = e => {
    const selected = {
      race : this.state.selected.race,
      class : e.target.value,
      alignment: this.state.selected.alignment
    };
    this.setState({ selected });
  };

  handleClassAttrChange = classFields => {
    const selected = {...this.state.selected, ...classFields};
    this.setState({ selected });
  };
}

export default App;