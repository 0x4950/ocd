// Run with 'npm run dev'.

const webpack = require('webpack');
const path = require("path");

const config = [
  {
    // Bundle for the character creation page.
    entry: __dirname + '/character-create-js/character-create.js',
    output: {
        path: path.join(__dirname, '/../server/app/static/dist/'),
        filename: 'character-create.js',
    },
    module: {
      rules: [
        {
          test: /\.js$/,
          exclude: /node_modules/,
          use: 'babel-loader'
        },
        {
          test: /\.jsx?$/,
          exclude: /node_modules/,
          use: 'babel-loader'
        },
      ]
    },
    resolve: {
      extensions: ['.js', '.jsx', '.css']
    },
  },
  {
    // Bundle for the dashboard page.
    entry: __dirname + '/dashboard-js/dashboard.js',
    output: {
        path: path.join(__dirname, '/../server/app/static/dist/'),
        filename: 'dashboard.js',
    },
    module: {
      rules: [
        {
          test: /\.js$/,
          exclude: /node_modules/,
          use: 'babel-loader'
        },
        {
          test: /\.jsx?$/,
          exclude: /node_modules/,
          use: 'babel-loader'
        },
      ]
    },
    resolve: {
      extensions: ['.js', '.jsx', '.css']
    },
  }
];

module.exports = config;