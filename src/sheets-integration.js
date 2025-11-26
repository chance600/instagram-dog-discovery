const { google } = require('googleapis');
const config = require('./config');

class SheetsIntegration {
  constructor() {
    this.sheets = null;
    this.auth = null;
  }

  async authenticate() {
    try {
      this.auth = new google.auth.GoogleAuth({
        credentials: config.googleSheets.credentials,
        scopes: ['https://www.googleapis.com/auth/spreadsheets']
      });
      this.sheets = google.sheets({ version: 'v4', auth: this.auth });
      console.log('✓ Authenticated with Google Sheets');
      return true;
    } catch (error) {
      console.error('Authentication failed:', error.message);
      return false;
    }
  }

  async getExistingUsernames() {
    try {
      const response = await this.sheets.spreadsheets.values.get({
        spreadsheetId: config.googleSheets.spreadsheetId,
        range: `${config.googleSheets.sheetName}!A:A`
      });

      const rows = response.data.values || [];
      const usernames = rows.slice(1).map(row => row[0]).filter(Boolean);
      console.log(`✓ Found ${usernames.length} existing accounts in sheet`);
      return usernames;
    } catch (error) {
      console.error('Failed to get existing usernames:', error.message);
      return [];
    }
  }

  async appendAccounts(accounts) {
    try {
      if (accounts.length === 0) {
        console.log('No new accounts to add');
        return 0;
      }

      const existingUsernames = await this.getExistingUsernames();
      const newAccounts = accounts.filter(
        acc => !existingUsernames.includes(acc.username)
      );

      if (newAccounts.length === 0) {
        console.log('All accounts already exist in sheet');
        return 0;
      }

      const rows = newAccounts.map(acc => [
        acc.username,
        acc.followers,
        new Date().toISOString(),
        'dog_video'
      ]);

      await this.sheets.spreadsheets.values.append({
        spreadsheetId: config.googleSheets.spreadsheetId,
        range: `${config.googleSheets.sheetName}!A:D`,
        valueInputOption: 'RAW',
        resource: { values: rows }
      });

      console.log(`✓ Added ${newAccounts.length} new accounts to sheet`);
      newAccounts.forEach(acc => {
        console.log(`  - @${acc.username}`);
      });
      return newAccounts.length;
    } catch (error) {
      console.error('Failed to append accounts:', error.message);
      return 0;
    }
  }
}

module.exports = SheetsIntegration;
