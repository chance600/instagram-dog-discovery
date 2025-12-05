#!/usr/bin/env python3
"""
Dog Content Discovery Pipeline
Fetches dog-related content from Reddit and YouTube using official APIs
and appends results to Google Sheets.
"""

import os base64
import sys
import json
import logging
from datetime import datetime
from typing import List, Dict, Set
import praw
from googleapiclient.discovery import build
from google.oauth2 import service_account
import gspread
from gspread.exceptions import APIError

# Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
MAX_RESULTS_PER_SOURCE = int(os.getenv('MAX_RESULTS', '50'))
SHEET_NAME = os.getenv('SHEET_NAME', 'Sheet1')

# Reddit Configuration
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'DogContentDiscovery/1.0')

# YouTube Configuration  
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# Google Sheets Configuration
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')

# Dog-related subreddits to monitor
DOG_SUBREDDITS = [
    'dogs',
    'dogtraining', 
    'DogAdvice',
    'puppy101',
    'Dogtraining',
    'lookatmydog',
    'dogpictures',
    'dogswithjobs',
    'rarepuppers'
]

# YouTube search queries
YOUTUBE_SEARCH_QUERIES = [
    'dog training tips',
    'dog rescue stories',
    'dog breeds guide',
    'puppy training'
]

# Minimum thresholds
REDDIT_MIN_SUBSCRIBERS = 1000
YOUTUBE_MIN_SUBSCRIBERS = 5000

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DogContentFetcher:
    """Main class for fetching dog content from multiple sources."""
    
    def __init__(self):
        self.reddit = None
        self.youtube = None
        self.sheets_client = None
        self.worksheet = None
        self.existing_urls: Set[str] = set()
        
    def validate_credentials(self) -> bool:
        """Validate that all required credentials are present."""
        logger.info("✓ Validating credentials...")
        
        missing = []
        if not REDDIT_CLIENT_ID:
            missing.append('REDDIT_CLIENT_ID')
        if not REDDIT_CLIENT_SECRET:
            missing.append('REDDIT_CLIENT_SECRET')
        if not YOUTUBE_API_KEY:
            missing.append('YOUTUBE_API_KEY')
        if not GOOGLE_CREDENTIALS_JSON:
            missing.append('GOOGLE_CREDENTIALS')
        if not SPREADSHEET_ID:
            missing.append('SPREADSHEET_ID')
            
        if missing:
            logger.error(f"✗ Missing credentials: {', '.join(missing)}")
            return False
            
        logger.info("✓ All credentials present")
        return True
        
    def initialize_clients(self) -> bool:
        """Initialize Reddit, YouTube, and Google Sheets clients."""
        logger.info("✓ Initializing API clients...")
        
        try:
            # Initialize Reddit
            self.reddit = praw.Reddit(
                client_id=REDDIT_CLIENT_ID,
                client_secret=REDDIT_CLIENT_SECRET,
                user_agent=REDDIT_USER_AGENT
            )
            logger.info("✓ Reddit client initialized")
            
            # Initialize YouTube
            self.youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
            logger.info("✓ YouTube client initialized")
            
            # Initialize Google Sheets
            # Try base64 decoding first, then fallback to plain JSON
            try:
                creds_json = base64.b64decode(GOOGLE_CREDENTIALS_JSON).decode('utf-8')
            except Exception:
                creds_json = GOOGLE_CREDENTIALS_JSON
            creds_dict = json.loads(creds_json)            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self.sheets_client = gspread.authorize(credentials)
            spreadsheet = self.sheets_client.open_by_key(SPREADSHEET_ID)
            self.worksheet = spreadsheet.worksheet(SHEET_NAME)
            logger.info("✓ Google Sheets client initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to initialize clients: {str(e)}")
            return False
        
    def load_existing_urls(self) -> None:
        """Load existing URLs from sheet to avoid duplicates."""
        logger.info("✓ Loading existing URLs from sheet...")
        
        try:
            all_values = self.worksheet.get_all_values()
            if len(all_values) > 1:  # Skip header row
                for row in all_values[1:]:
                    if len(row) > 3 and row[3]:  # URL column (D)
                        self.existing_urls.add(row[3].strip())
            
            logger.info(f"✓ Loaded {len(self.existing_urls)} existing URLs")
            
        except Exception as e:
            logger.warning(f"⚠ Could not load existing URLs: {str(e)}")
    
    def categorize_content(self, title: str, description: str) -> str:
        """Auto-categorize content based on keywords."""
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ['train', 'obedience', 'behavior', 'command']):
            return 'training'
        elif any(word in text for word in ['rescue', 'adopt', 'shelter', 'save']):
            return 'rescue'
        elif any(word in text for word in ['puppy', 'puppies', 'newborn']):
            return 'puppies'
        elif any(word in text for word in ['breed', 'breeds', 'golden', 'labrador', 'husky']):
            return 'breeds'
        elif any(word in text for word in ['funny', 'cute', 'adorable', 'hilarious']):
            return 'funny'
        elif any(word in text for word in ['health', 'vet', 'medical', 'care']):
            return 'health'
        else:
            return 'general'
    
    def fetch_reddit_content(self) -> List[Dict]:
        """Fetch dog-related content from Reddit."""
        logger.info("✓ Fetching content from Reddit...")
        results = []
        
        try:
            # Fetch subreddit information
            for sub_name in DOG_SUBREDDITS:
                try:
                    subreddit = self.reddit.subreddit(sub_name)
                    
                    # Get subreddit details
                    if subreddit.subscribers >= REDDIT_MIN_SUBSCRIBERS:
                        url = f"https://reddit.com/r/{sub_name}"
                        
                        if url not in self.existing_urls:
                            results.append({
                                'platform': 'Reddit',
                                'source_type': 'subreddit',
                                'username': f"r/{sub_name}",
                                'url': url,
                                'followers': subreddit.subscribers,
                                'description': subreddit.public_description[:200] if subreddit.public_description else '',
                                'category': 'community'
                            })
                            logger.info(f"  ✓ Found subreddit: r/{sub_name} ({subreddit.subscribers:,} members)")
                        
                except Exception as e:
                    logger.warning(f"  ⚠ Could not fetch r/{sub_name}: {str(e)}")
                    continue
            
            # Fetch active posters
            for sub_name in DOG_SUBREDDITS[:3]:  # Limit to top 3 subs
                try:
                    subreddit = self.reddit.subreddit(sub_name)
                    for post in subreddit.hot(limit=10):
                        author = post.author
                        if author and hasattr(author, 'name'):
                            url = f"https://reddit.com/user/{author.name}"
                            if url not in self.existing_urls:
                                try:
                                    # Get author karma as proxy for followers
                                    karma = author.link_karma + author.comment_karma
                                    if karma >= 1000:
                                        results.append({
                                            'platform': 'Reddit',
                                            'source_type': 'user',
                                            'username': f"u/{author.name}",
                                            'url': url,
                                            'followers': karma,
                                            'description': f"Active poster in r/{sub_name}",
                                            'category': 'content_creator'
                                        })
                                        logger.info(f"  ✓ Found user: u/{author.name} ({karma:,} karma)")
                                except Exception:
                                    continue
                                    
                except Exception as e:
                    logger.warning(f"  ⚠ Could not fetch posts from r/{sub_name}: {str(e)}")
                    continue
            
            logger.info(f"✓ Found {len(results)} new Reddit sources")
            return results[:MAX_RESULTS_PER_SOURCE]
            
        except Exception as e:
            logger.error(f"✗ Reddit fetch failed: {str(e)}")
            return []
    
    def fetch_youtube_content(self) -> List[Dict]:
        """Fetch dog-related content from YouTube."""
        logger.info("✓ Fetching content from YouTube...")
        results = []
        
        try:
            for query in YOUTUBE_SEARCH_QUERIES:
                try:
                    # Search for channels
                    search_response = self.youtube.search().list(
                        q=query,
                        type='channel',
                        part='id,snippet',
                        maxResults=10
                    ).execute()
                    
                    for item in search_response.get('items', []):
                        channel_id = item['id']['channelId']
                        
                        # Get channel statistics
                        channel_response = self.youtube.channels().list(
                            part='statistics,snippet',
                            id=channel_id
                        ).execute()
                        
                        if channel_response.get('items'):
                            channel = channel_response['items'][0]
                            stats = channel.get('statistics', {})
                            snippet = channel.get('snippet', {})
                            
                            subscriber_count = int(stats.get('subscriberCount', 0))
                            
                            if subscriber_count >= YOUTUBE_MIN_SUBSCRIBERS:
                                url = f"https://youtube.com/channel/{channel_id}"
                                
                                if url not in self.existing_urls:
                                    channel_title = snippet.get('title', '')
                                    description = snippet.get('description', '')[:200]
                                    
                                    results.append({
                                        'platform': 'YouTube',
                                        'source_type': 'channel',
                                        'username': channel_title,
                                        'url': url,
                                        'followers': subscriber_count,
                                        'description': description,
                                        'category': self.categorize_content(channel_title, description)
                                    })
                                    logger.info(f"  ✓ Found channel: {channel_title} ({subscriber_count:,} subscribers)")
                    
                except Exception as e:
                    logger.warning(f"  ⚠ Could not fetch YouTube results for '{query}': {str(e)}")
                    continue
            
            logger.info(f"✓ Found {len(results)} new YouTube channels")
            return results[:MAX_RESULTS_PER_SOURCE]
            
        except Exception as e:
            logger.error(f"✗ YouTube fetch failed: {str(e)}")
            return []
    
    def append_to_sheet(self, data: List[Dict]) -> int:
        """Append new data to Google Sheet."""
        if not data:
            logger.info("⚠ No new data to append")
            return 0
        
        logger.info(f"✓ Appending {len(data)} rows to sheet...")
        
        try:
            date_added = datetime.now().strftime('%Y-%m-%d')
            
            rows = []
            for item in data:
                row = [
                    item.get('platform', ''),
                    item.get('source_type', ''),
                    item.get('username', ''),
                    item.get('url', ''),
                    item.get('followers', 0),
                    item.get('description', ''),
                    date_added,
                    item.get('category', '')
                ]
                rows.append(row)
            
            self.worksheet.append_rows(rows, value_input_option='USER_ENTERED')
            logger.info(f"✓ Successfully appended {len(rows)} rows")
            return len(rows)
            
        except APIError as e:
            logger.error(f"✗ Google Sheets API error: {str(e)}")
            return 0
        except Exception as e:
            logger.error(f"✗ Failed to append to sheet: {str(e)}")
            return 0
    
    def run(self) -> Dict:
        """Main execution method."""
        logger.info("="*60)
        logger.info("🐶 Dog Content Discovery Pipeline Starting")
        logger.info("="*60)
        
        # Validate credentials
        if not self.validate_credentials():
            logger.error("✗ Credential validation failed. Exiting.")
            return {'success': False, 'error': 'Missing credentials'}
        
        # Initialize clients
        if not self.initialize_clients():
            logger.error("✗ Client initialization failed. Exiting.")
            return {'success': False, 'error': 'Initialization failed'}
        
        # Load existing URLs
        self.load_existing_urls()
        
        # Fetch content from all sources
        all_content = []
        
        reddit_content = self.fetch_reddit_content()
        all_content.extend(reddit_content)
        
        youtube_content = self.fetch_youtube_content()
        all_content.extend(youtube_content)
        
        # Append to sheet
        rows_added = self.append_to_sheet(all_content)
        
        # Summary
        logger.info("="*60)
        logger.info("🎉 Pipeline Complete!")
        logger.info(f"✓ Reddit sources found: {len(reddit_content)}")
        logger.info(f"✓ YouTube channels found: {len(youtube_content)}")
        logger.info(f"✓ Total rows added to sheet: {rows_added}")
        logger.info("="*60)
        
        return {
            'success': True,
            'reddit_count': len(reddit_content),
            'youtube_count': len(youtube_content),
            'total_added': rows_added
        }


def main():
    """Main entry point."""
    fetcher = DogContentFetcher()
    result = fetcher.run()
    
    if not result['success']:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
