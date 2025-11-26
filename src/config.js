module.exports = {
  instagram: {
    username: process.env.INSTAGRAM_USERNAME,
    password: process.env.INSTAGRAM_PASSWORD,
    searchHashtags: ['dogsofinstagram', 'dogvideos', 'puppiesofinstagram', 'doglife', 'dogsofig'],
    minFollowers: 500,
    maxAccountsPerRun: 5
  },
  googleSheets: {
    spreadsheetId: process.env.GOOGLE_SHEETS_ID || '1zjGGHpPT-6nNnn36EIzjC38JPBT9HwD7TSHLjYa2YP4',
    sheetName: 'Sheet1',
    credentials: process.env.GOOGLE_CREDENTIALS ? JSON.parse(process.env.GOOGLE_CREDENTIALS) : null
  },
  delays: {
    minActionDelay: 2000,
    maxActionDelay: 5000,
    minScrollDelay: 1000,
    maxScrollDelay: 3000
  }
};
