# 🐕 Dog Content Discovery & Engagement System - n8n Setup Guide

## Overview

This guide will help you set up an advanced AI-powered automation system for discovering dog-related content on Reddit and YouTube, with intelligent engagement capabilities. The system uses n8n hosted on Google Cloud's free tier and integrates with Google Sheets for data management.

## ✨ Features

- **Multi-Platform Discovery**: Automatically finds dog content on Reddit and YouTube
- **AI-Powered Categorization**: Uses Google Gemini to intelligently categorize content
- **Smart Deduplication**: Prevents duplicate entries in your database
- **Ethical Auto-Commenting**: AI drafts relevant, helpful comments (with human review)
- **Scheduled Execution**: Runs biweekly (Monday & Thursday at 9 AM UTC)
- **100% Free Hosting**: Runs on Google Cloud's Always Free tier

## 🏗️ Architecture

```
┌─────────────────┐
│  Cloud Scheduler│
│  (Biweekly)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│   n8n Instance  │────▶│ Reddit API   │
│  (GCP e2-micro) │     └──────────────┘
│                 │
│                 │     ┌──────────────┐
│                 │────▶│ YouTube API  │
│                 │     └──────────────┘
│                 │
│                 │     ┌──────────────┐
│                 │────▶│ Google Gemini│
│                 │     │ (AI Agent)   │
│                 │     └──────────────┘
│                 │
│                 │     ┌──────────────┐
│                 │────▶│ Google Sheets│
└─────────────────┘     │ (Database)   │
                        └──────────────┘
```

## 📋 Prerequisites

1. **Google Cloud Account** (with billing enabled for free tier verification)
2. **Reddit Developer Account** - Create at https://www.reddit.com/prefs/apps
3. **YouTube Data API Key** - Get from Google Cloud Console
4. **Google Gemini API Key** - Already available in your GCP project
5. **Google Sheets Service Account** - Already configured
6. **Domain Name** (optional but recommended for SSL)

## 🚀 Quick Start

### Step 1: Deploy n8n on Google Cloud Free Tier

1. **Create a VM Instance**:
   ```bash
   gcloud compute instances create n8n-dog-discovery \
     --zone=us-west1-b \
     --machine-type=e2-micro \
     --image-family=ubuntu-2204-lts \
     --image-project=ubuntu-os-cloud \
     --boot-disk-size=30GB \
     --boot-disk-type=pd-standard \
     --tags=http-server,https-server
   ```

2. **SSH into the instance**:
   ```bash
   gcloud compute ssh n8n-dog-discovery --zone=us-west1-b
   ```

3. **Install Docker and Docker Compose**:
   ```bash
   # Update packages
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose
   
   # Add user to docker group
   sudo usermod -aG docker $USER
   newgrp docker
   ```

4. **Create n8n directory and docker-compose file**:
   ```bash
   mkdir -p ~/n8n
   cd ~/n8n
   nano docker-compose.yml
   ```

5. **Add this configuration**:
   ```yaml
   version: '3.8'
   
   services:
     n8n:
       image: n8nio/n8n:latest
       container_name: n8n
       restart: always
       ports:
         - "5678:5678"
       environment:
         - N8N_BASIC_AUTH_ACTIVE=true
         - N8N_BASIC_AUTH_USER=admin
         - N8N_BASIC_AUTH_PASSWORD=ChangeMeToSecurePassword123!
         - N8N_HOST=0.0.0.0
         - WEBHOOK_URL=http://YOUR_VM_IP:5678/
         - GENERIC_TIMEZONE=America/New_York
         - N8N_METRICS=true
       volumes:
         - ./n8n_data:/home/node/.n8n
   ```

6. **Start n8n**:
   ```bash
   docker-compose up -d
   ```

7. **Configure Firewall**:
   ```bash
   gcloud compute firewall-rules create allow-n8n \
     --allow tcp:5678 \
     --source-ranges 0.0.0.0/0 \
     --target-tags http-server
   ```

### Step 2: Configure API Credentials

#### Reddit API Setup

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in:
   - **Name**: Dog Content Discovery Bot
   - **Type**: Script
   - **Description**: Automated dog content discovery
   - **Redirect URI**: http://localhost:8080 (required but not used)
4. Save and note:
   - **Client ID** (under app name)
   - **Client Secret** (visible after creation)

#### YouTube Data API Setup

1. Go to Google Cloud Console
2. Enable YouTube Data API v3
3. Create API Key (restrict to YouTube Data API v3)
4. Note the API key

#### Google Sheets Service Account

You already have this configured! Use the existing:
- Service account email: `dog-content-discovery@...iam.gserviceaccount.com`
- JSON credentials stored in GitHub Secrets

### Step 3: Import n8n Workflows

1. Access n8n at `http://YOUR_VM_IP:5678`
2. Login with credentials from docker-compose.yml
3. Import the workflows from this repository:
   - `n8n-workflows/reddit-youtube-discovery.json`
   - `n8n-workflows/ai-comment-drafter.json`

### Step 4: Configure Credentials in n8n

1. **Reddit OAuth2**:
   - Credentials Type: OAuth2 API
   - Client ID: `[from Reddit app]`
   - Client Secret: `[from Reddit app]`
   - Scope: `read submit`

2. **YouTube**:
   - API Key: `[from Google Cloud Console]`

3. **Google Gemini**:
   - API Key: `[from your GCP project]`

4. **Google Sheets**:
   - Service Account JSON: `[your existing credentials]`

### Step 5: Configure Cloud Scheduler

```bash
# Create scheduler for Monday 9 AM UTC
gcloud scheduler jobs create http dog-discovery-monday \
  --location=us-central1 \
  --schedule="0 9 * * 1" \
  --uri="http://YOUR_VM_IP:5678/webhook/dog-discovery" \
  --http-method=POST

# Create scheduler for Thursday 9 AM UTC
gcloud scheduler jobs create http dog-discovery-thursday \
  --location=us-central1 \
  --schedule="0 9 * * 4" \
  --uri="http://YOUR_VM_IP:5678/webhook/dog-discovery" \
  --http-method=POST
```

## 📊 Workflow Details

### Workflow 1: Reddit & YouTube Discovery

**Trigger**: Webhook (called by Cloud Scheduler or manually)

**Steps**:
1. **Fetch Reddit Posts**: Search dog-related subreddits
   - Subreddits: `dogs`, `dogtraining`, `puppy101`, `DogCare`, etc.
   - Filter: Posts with 50+ upvotes from last 7 days

2. **Fetch YouTube Channels**: Search for dog content creators
   - Keywords: "dog training", "puppy care", "dog behavior"
   - Filter: Channels with 5000+ subscribers

3. **AI Categorization** (Google Gemini):
   - Categories: Training, Health, Breeds, Adoption, General
   - Extract key information
   - Rate relevance (1-10)

4. **Deduplication Check**:
   - Query last 500 rows in Google Sheet
   - Skip if URL already exists

5. **Append to Google Sheets**:
   - Sheet: "Research Groups Database"
   - Columns: Platform, Source_Type, Username, URL, Followers, Description, Date_Added, Category, AI_Score

### Workflow 2: AI Comment Drafter (Optional)

**Trigger**: Manual or scheduled

**Steps**:
1. **Fetch High-Value Posts** from Google Sheet (AI_Score >= 8)
2. **Draft Comments** using Google Gemini:
   - Analyze post content
   - Generate helpful, relevant comment
   - Include subtle brand mention if appropriate
3. **Human Review**:
   - Save drafts to separate sheet
   - Flag for manual approval
4. **Post Approved Comments** (after human review)

## 🔒 Security Best Practices

1. **Change Default Passwords**: Update n8n admin password immediately
2. **Use SSL**: Configure Let's Encrypt for HTTPS (optional)
3. **Restrict Firewall**: Limit IP access if possible
4. **Rate Limiting**: Configure delays between API calls
5. **API Key Rotation**: Rotate keys every 90 days

## 💰 Cost Optimization

- **VM**: e2-micro (Always Free: 1 instance)
- **Storage**: 30GB standard disk (Always Free: 30GB)
- **Egress**: ~1GB/month (Always Free: 1GB)
- **Cloud Scheduler**: 3 free jobs/month
- **Total Monthly Cost**: $0

## 🎯 Customization

### Add More Subreddits

Edit the Reddit node in n8n:
```json
{
  "subreddits": ["dogs", "dogtraining", "puppy101", "DogCare", "reactivedogs"]
}
```

### Adjust Discovery Frequency

Modify Cloud Scheduler cron:
- Daily: `0 9 * * *`
- Weekly: `0 9 * * 1`
- Every 6 hours: `0 */6 * * *`

### Change AI Categorization

Update Gemini prompt in n8n:
```
Analyze this dog-related content and categorize it into:
1. Dog Training
2. Dog Health & Nutrition
3. Dog Breeds & Behavior
4. Dog Adoption & Rescue
5. General Dog Care

Provide a relevance score (1-10) and brief reasoning.
```

## 🐛 Troubleshooting

### n8n Won't Start
```bash
cd ~/n8n
docker-compose logs -f
```

### Reddit API 401 Unauthorized
- Verify app type is "Script" not "Web App"
- Check client ID and secret
- Regenerate credentials if needed

### YouTube API 403 Forbidden
- Check API key restrictions
- Verify YouTube Data API v3 is enabled
- Check quota limits (10,000 units/day)

### Google Sheets Permission Denied
- Verify service account email is added as Editor
- Check JSON credentials are valid
- Ensure Sheets API is enabled

## 📈 Monitoring

### Check n8n Logs
```bash
docker logs n8n -f
```

### Monitor VM Resources
```bash
# CPU and Memory
htop

# Disk Usage
df -h
```

### View Execution History
- n8n UI → Executions tab
- Filter by status: Success/Error
- Review error messages

## 🔄 Maintenance

### Update n8n
```bash
cd ~/n8n
docker-compose pull
docker-compose up -d
```

### Backup Data
```bash
# Backup n8n workflows and credentials
tar -czf n8n-backup-$(date +%Y%m%d).tar.gz ~/n8n/n8n_data/
```

### Clean Old Data
```bash
# Clear old execution data (optional)
docker exec -it n8n n8n execute --file cleanup-executions.json
```

## 🎓 Advanced: Alternative Hosting Options

### Option 1: Render.com (Free Tier)
- 750 hours/month free
- Automatic SSL
- Easier setup (no VM management)
- Guide: See `RENDER_DEPLOYMENT.md`

### Option 2: Railway (Free $5 credit)
- Simple deployment from GitHub
- Automatic HTTPS
- Built-in PostgreSQL

### Option 3: Oracle Cloud (Always Free)
- More generous limits
- 2 micro instances
- 200GB storage

## 📚 Resources

- **n8n Documentation**: https://docs.n8n.io/
- **Reddit API**: https://www.reddit.com/dev/api/
- **YouTube Data API**: https://developers.google.com/youtube/v3
- **Google Gemini**: https://ai.google.dev/
- **Community Workflows**: https://n8n.io/workflows/

## 🤝 Contributing

Found improvements? Submit a PR with:
- Better AI prompts
- Additional data sources
- Enhanced categorization logic
- Cost optimizations

## ⚖️ Ethical Guidelines

When using auto-commenting features:

1. **Add Value**: Only comment when you have helpful information
2. **Be Transparent**: Disclose if using automation
3. **Human Review**: Always review AI-generated comments
4. **Respect Communities**: Follow subreddit rules
5. **Rate Limiting**: Don't spam or overwhelm communities
6. **No Deception**: Don't impersonate humans or manipulate votes

## 📝 License

MIT License - Free to use and modify

---

**Questions?** Open an issue on GitHub

**Updates?** Watch this repo for improvements
