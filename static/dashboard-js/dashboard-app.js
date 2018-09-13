import React, { Component } from 'react';

class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      campaignsList: []
    };
  }

  componentDidMount() {
    fetch('http://localhost:5000/api/games/')
      .then(response => response.json())
      .then(campaignsList => this.setState({ campaignsList }));
  }

  render() {
    return (
      <React.Fragment>
        {this.state.campaignsList.map(campaign => <div>{campaign.name}, {campaign.date}</div>)}
      </React.Fragment>
    );
  }
}

export default App;