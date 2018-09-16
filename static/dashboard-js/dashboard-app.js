import React, { Component } from 'react';

class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
      campaignsList: [],
      campaingName: '',
      canCreate: true
    };
  }

  componentDidMount() {
    fetch('http://localhost:5000/api/campaings/')
      .then(response => response.json())
      .then(campaignsList => this.setState({ campaignsList}))
      .catch(error => console.log('Error:', error));
  }

  render() {
    return (
      <React.Fragment>
        <div id="games_list">
          <div id="games_header">
            <h1>Campaigns</h1>
          </div>
          <div id="actual_list">
            {this.state.campaignsList.map(campaign => {
              return (
                <div key={campaign.id} class="game_div">
                  <label for={campaign.name}></label>
                  <a class="game_link" href={ 'http://localhost:5000/campaign/' + campaign.id}>
                    {campaign.name}
                    <span class="create_date">Created on: { campaign.created_time}</span>
                  </a>
                </div>
              )
            })}
          </div>
        </div>

        <div>
          <input type="text" onChange={this.handleNameChange} placeholder="Campaign name"></input>
          <button onClick={this.createNewCampaign}>Create new campaign</button>
          <p hidden={this.state.canCreate}>You cannot.</p>
          <button onClick={this.logout}>Sign out</button>
        </div>
      </React.Fragment>
    );
  }

  createNewCampaign = () => {
    fetch('http://localhost:5000/api/campaings/', {
      method: 'POST',
      body: JSON.stringify({'name': this.state.campaingName}),
      headers: {
        'Content-Type': 'application/json'
    }})
      .then(response => response.json())
      .then(campaignsList => {
        this.setState({ campaignsList});
        this.setState({ canCreate: true});
      })
      .catch(error => this.setState({ canCreate: false }));
  };

  handleNameChange = e => {
    this.setState({ campaingName: e.target.value });
  };

  logout = () => {
    window.location.replace("http://localhost:5000/logout/");
  };
}

export default App;