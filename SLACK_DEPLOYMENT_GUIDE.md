# Slack + CTO Council Deployment Guide

Deploy your CTO Council as a Slack bot that your team can use directly in Slack!

---

## Overview

Your CTO Council is now configured to:
1. **Listen to messages** in your Slack channel (`#mapache-agents`)
2. **Run the 3-stage council process** (Responses → Peer Evaluation → Synthesis)
3. **Post threaded responses** with all stages visible
4. **Store conversations** in Firestore for history/audit

---

## Prerequisites

✅ **You Already Have:**
- Google Cloud project: `mapache-app`
- Slack workspace: `T07B3RRNQ87`
- Slack channel: `#mapache-agents` (ID: `C07BLSVMP9S`)
- Slack bot name: `cto council`
- OpenRouter API key configured
- Backend running with Firebase/Firestore

⚠️ **You Need:**
- Slack Admin access (you said you have this)
- Google Cloud CLI access (for deployment)

---

## Step 1: Create Slack Bot App (5 minutes)

### 1.1: Go to Slack App Directory
1. Open: https://api.slack.com/apps
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. App name: `cto council`
5. Workspace: Select your workspace
6. Click **Create App**

### 1.2: Get Your Credentials
After creating the app, you'll see:
- **Bot Token** (starts with `xoxb-`)
- **Signing Secret**

**Copy both of these - you'll need them!**

### 1.3: Set Event Request URL
1. In your Slack app settings, go to **"Event Subscriptions"**
2. Toggle **"Enable Events"** to ON
3. In **"Request URL"** field, enter:
   ```
   https://your-project-id.cloudfunctions.net/on_message
   ```
   (We'll provide the actual URL after deployment)

### 1.4: Subscribe to Bot Events
Under **"Subscribe to bot events"**, add:
- `message.channels` - Messages in channels
- `message.im` - Direct messages

Click **Save**

### 1.5: Set Bot Permissions
1. Go to **"OAuth & Permissions"**
2. Under **"Scopes"** → **"Bot Token Scopes"**, add:
   - `chat:write` - Send messages
   - `channels:read` - Read channel info
   - `im:read` - Read DMs

3. Go to **"Install App"** and follow the prompts
4. Copy the **Bot Token** (starts with `xoxb-`)

---

## Step 2: Create Google Cloud Secrets

Now you'll store your Slack credentials in Google Cloud so the bot can access them.

### Using Google Cloud Console (No CLI):

1. Go to: https://console.cloud.google.com/
2. Select project: `mapache-app`
3. Search for **"Secret Manager"**
4. Click **"Create Secret"**

**Create Secret 1: SLACK_BOT_TOKEN**
- Name: `SLACK_BOT_TOKEN`
- Value: `xoxb-your-bot-token-here`
- Click **Create**

**Create Secret 2: SLACK_SIGNING_SECRET**
- Name: `SLACK_SIGNING_SECRET`
- Value: `your-signing-secret-here`
- Click **Create**

---

## Step 3: Deploy Backend to Google Cloud

### 3.1: Update Requirements
Your backend now uses these dependencies. Update `pyproject.toml`:

```
[project]
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "python-dotenv>=1.0.0",
    "aiohttp>=3.8.0",
    "pydantic>=2.9.0",
    "firebase-admin>=6.2.0",
    "httpx>=0.27.0",  # Added for Slack HTTP requests
]
```

### 3.2: Deploy Using Google Cloud Console

1. Go to: https://console.cloud.google.com/functions
2. Click **"Create Function"**
3. Configure:
   - **Name**: `cto-council-slack`
   - **Region**: `us-central1`
   - **Trigger**: `HTTPS`
   - **Runtime**: `Python 3.12`

4. Copy the code from `backend/main.py` and `backend/slack_handler.py`
5. For `requirements.txt`, use:
   ```
   fastapi>=0.115.0
   uvicorn[standard]>=0.32.0
   aiohttp>=3.8.0
   pydantic>=2.9.0
   firebase-admin>=6.2.0
   httpx>=0.27.0
   python-dotenv>=1.0.0
   ```

6. Set **Entry point**: `app`
7. Under **Runtime settings**, add environment variables:
   ```
   OPENROUTER_API_KEY=your-api-key
   SLACK_BOT_TOKEN=xoxb-your-token
   SLACK_SIGNING_SECRET=your-secret
   GCLOUD_PROJECT=mapache-app
   ```

8. Click **Deploy**

### 3.3: Get Your HTTPS URL

After deployment, Google Cloud gives you an HTTPS URL like:
```
https://us-central1-mapache-app.cloudfunctions.net/cto-council-slack
```

---

## Step 4: Update Slack with Your Function URL

1. Go back to: https://api.slack.com/apps
2. Click your app
3. Go to **"Event Subscriptions"**
4. Update **"Request URL"** with your Google Cloud function URL
5. Slack will verify the URL
6. Click **Save**

---

## Step 5: Invite Bot to Channel

1. Go to your Slack workspace
2. In `#mapache-agents` channel, type: `@cto council`
3. Click the bot name and select **"View App Details"**
4. Click **"Add to channel"** or just invite it: `/invite @cto council`

---

## Step 6: Test It!

### In Slack:
1. Go to `#mapache-agents`
2. Type your question:
   ```
   We're a startup with 50,000 users and our monolithic Rails application
   is becoming hard to maintain. Our team is proposing we migrate to microservices.
   What should we consider before making this decision?
   ```

3. Hit **Send**
4. The bot will respond with:
   - **Thread 1**: Stage 1 (4 individual CTO responses)
   - **Thread 2**: Stage 2 (Peer rankings from each CTO)
   - **Thread 3**: Stage 3 (Final synthesized answer)

### Each message shows:
- 🔵 Orchestrator
- 🟢 Architect
- 🔴 Mentor
- 🟣 Visionary

---

## Troubleshooting

### Bot Doesn't Respond

1. **Check function logs**:
   - Go to: https://console.cloud.google.com/functions
   - Click your function
   - View **"Logs"**
   - Look for errors

2. **Verify webhook**:
   - In Slack app settings, go to **"Event Subscriptions"**
   - Check if URL shows ✅ "Verified"
   - If not, check logs for verification error

3. **Check secrets**:
   - Verify `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` are set in function environment

4. **Test endpoint**:
   - Open in browser: `https://your-function-url/health/slack`
   - Should show: `{"status":"ok","slack_configured":true}`

### Messages Post But No Council Response

1. Check Google Cloud function logs
2. Verify OpenRouter API key is working
3. Check Firestore has write permissions

### Firestore Errors

1. Go to: https://console.cloud.google.com/firestore
2. Check **"Rules"** tab
3. Should allow writes from Cloud Functions

---

## Architecture Summary

```
Slack Message
    ↓
Google Cloud Function (on_message)
    ↓
SlackHandler.handle_message()
    ↓
Create Firestore conversation
    ↓
Run 3-stage council process
    ↓
Format responses as Slack blocks
    ↓
Post threaded messages to Slack
    ↓
Save to Firestore
```

---

## Files Created

- `backend/slack_config.py` - Slack configuration
- `backend/slack_handler.py` - Handles Slack events
- `backend/slack_formatter.py` - Formats responses for Slack
- `backend/main.py` - Updated with `/slack/events` endpoint

---

## Next Steps

1. ✅ Create Slack bot app
2. ✅ Get bot token and signing secret
3. ✅ Create Google Cloud secrets
4. ✅ Deploy to Cloud Functions
5. ✅ Update Slack webhook URL
6. ✅ Invite bot to channel
7. ✅ Test in Slack!

---

## Support

If something isn't working:
1. Check Google Cloud function logs
2. Verify all credentials are set correctly
3. Make sure Slack bot has permissions
4. Test endpoint health: `/health/slack`

