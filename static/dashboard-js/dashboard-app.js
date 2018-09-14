import React, { Component } from 'react';

class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      campaignsList: [],
      canCreate: true,
    };
  }

  componentDidMount() {
    fetch('http://localhost:5000/api/get_and_create_games/')
      .then(response => response.json())
      .then(campaignsList => this.setState({ campaignsList }))
      .catch(error => console.log(error));
  }

  render() {
    return (
      <React.Fragment>
        {this.state.campaignsList.map(campaign => <div key={campaign.id}>{campaign.name}</div>)}
        <div>
          <input type="text" placeholder="Campaign name"></input>
          <button onClick={() => this.createNewCampaign('getReal')}>Create new campaign</button>
          <p hidden={this.state.canCreate}>You cannot.</p>
          <button onClick={this.logout}>Sign out</button>
        </div>
      </React.Fragment>
    );
  }

  createNewCampaign = name => {
    fetch('http://localhost:5000/api/get_and_create_games/', {
      method: 'POST',
      body: JSON.stringify({'name': name}),
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then(response => {
      if (response.ok) {
        campaignsList = response.json();
        this.setState({ campaignsList })
      } else {
        if(response.status === 600) {
          this.setState({ canCreate: false })
        }
      }
    });
  }

  logout = () => {
    window.location.replace("http://localhost:5000/logout/");
  }
}

export default App;