import React, { Component } from 'react';
import Footer from '../components/footer';

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
    this.state.campaignsList.map(campaign => {
      console.log(typeof(campaign.created_time));
      });
    return (
      <React.Fragment>
        
        <div className="container-fluid">
          <div className="row">
            <div className="col-sm-12">

              <div id="welcome_message">
                <h3>Welcome, user</h3>
              </div>

              <div id="games_list">
                <div id="games_header">
                  <h1>Campaigns</h1>
                </div>
              
              <div id="actual_list">
                {this.state.campaignsList.map(campaign => {
                  return (
                    <div key={campaign.id} className="game_div">
                      <label htmlFor={campaign.name}></label>
                      <a className="game_link" href={ 'http://localhost:5000/campaign/' + campaign.id}>
                        {campaign.name}
                        <span className="create_date">Created on: { campaign.created_time}</span>
                      </a>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    
      <Footer />
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