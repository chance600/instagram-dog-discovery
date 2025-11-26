const InstagramScraper = require('./instagram-scraper');
const SheetsIntegration = require('./sheets-integration');
const config = require('./config');

async function main() {
  console.log('▶ Instagram Dog Account Discovery Started');
  console.log(`Target: ${config.instagram.maxAccountsPerRun} new accounts\n`);

  const scraper = new InstagramScraper();
  const sheets = new SheetsIntegration();

  try {
    await scraper.init();
    console.log('✓ Browser initialized');

    const loginSuccess = await scraper.login();
    if (!loginSuccess) {
      throw new Error('Failed to login to Instagram');
    }

    await sheets.authenticate();

    const hashtag = config.instagram.searchHashtags[
      Math.floor(Math.random() * config.instagram.searchHashtags.length)
    ];
    
    await scraper.searchHashtag(hashtag);
    const accounts = await scraper.extractAccountsFromPosts(config.instagram.maxAccountsPerRun);

    console.log(`\n✓ Found ${accounts.length} dog video accounts`);

    const addedCount = await sheets.appendAccounts(accounts);
    console.log(`\n✅ Run completed: ${addedCount} new accounts added to sheet\n`);
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  } finally {
    await scraper.close();
  }
}

main();
