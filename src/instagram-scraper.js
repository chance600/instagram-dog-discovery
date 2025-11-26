const puppeteer = require('puppeteer');
const config = require('./config');

class InstagramScraper {
  constructor() {
    this.browser = null;
    this.page = null;
  }

  async init() {
    this.browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    this.page = await this.browser.newPage();
    await this.page.setViewport({ width: 1280, height: 800 });
  }

  async login() {
    try {
      await this.page.goto('https://www.instagram.com/accounts/login/', { waitUntil: 'networkidle2' });
      await this.randomDelay();

      await this.page.type('input[name="username"]', config.instagram.username, { delay: 100 });
      await this.randomDelay(500, 1000);
      await this.page.type('input[name="password"]', config.instagram.password, { delay: 100 });
      await this.randomDelay(500, 1000);

      await Promise.all([
        this.page.click('button[type="submit"]'),
        this.page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 30000 })
      ]);

      console.log('✓ Logged in successfully');
      await this.randomDelay(3000, 5000);
      return true;
    } catch (error) {
      console.error('Login failed:', error.message);
      return false;
    }
  }

  async searchHashtag(hashtag) {
    try {
      await this.page.goto(`https://www.instagram.com/explore/tags/${hashtag}/`, { waitUntil: 'networkidle2' });
      await this.randomDelay(2000, 4000);
      console.log(`✓ Navigated to #${hashtag}`);
      return true;
    } catch (error) {
      console.error(`Failed to search hashtag #${hashtag}:`, error.message);
      return false;
    }
  }

  async extractAccountsFromPosts(maxAccounts = 5) {
    const accounts = [];
    
    try {
      await this.page.waitForSelector('article', { timeout: 10000 });
      
      const posts = await this.page.$$('article a[href*="/p/"]');
      console.log(`Found ${posts.length} posts`);

      for (let i = 0; i < Math.min(posts.length, maxAccounts * 2); i++) {
        if (accounts.length >= maxAccounts) break;

        try {
          await posts[i].click();
          await this.randomDelay(2000, 3000);

          await this.page.waitForSelector('article', { timeout: 5000 });

          const accountData = await this.page.evaluate(() => {
            const usernameEl = document.querySelector('article a[href*="/"][role="link"]');
            const videoEl = document.querySelector('video');
            const followersEl = document.querySelector('a[href*="/followers/"] span');
            
            if (!usernameEl || !videoEl) return null;

            const username = usernameEl.getAttribute('href').replace(/\//g, '');
            const followers = followersEl ? followersEl.textContent : 'Unknown';
            
            return { username, followers, hasVideo: true };
          });

          if (accountData && accountData.hasVideo) {
            const isDuplicate = accounts.some(acc => acc.username === accountData.username);
            if (!isDuplicate) {
              accounts.push(accountData);
              console.log(`✓ Found account: @${accountData.username} (${accountData.followers} followers)`);
            }
          }

          await this.page.keyboard.press('Escape');
          await this.randomDelay(1000, 2000);
        } catch (error) {
          console.log(`Skipping post ${i}: ${error.message}`);
          await this.page.keyboard.press('Escape').catch(() => {});
          continue;
        }
      }
    } catch (error) {
      console.error('Error extracting accounts:', error.message);
    }

    return accounts;
  }

  async randomDelay(min = config.delays.minActionDelay, max = config.delays.maxActionDelay) {
    const delay = Math.floor(Math.random() * (max - min + 1)) + min;
    await new Promise(resolve => setTimeout(resolve, delay));
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
    }
  }
}

module.exports = InstagramScraper;
