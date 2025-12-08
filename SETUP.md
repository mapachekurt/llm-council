# LLM Council - Google Cloud Setup Guide

This guide walks you through setting up the LLM Council application with Firebase, Clerk authentication, and Google Cloud.

## Prerequisites

- Node.js 18+ and npm
- Firebase CLI (`npm install -g firebase-tools`)
- A Google Cloud account
- A Clerk account (for authentication)
- An OpenRouter API account

## Step 1: Create a Clerk Application

1. Go to [clerk.com](https://clerk.com) and sign up
2. Create a new application
3. Note your **Publishable Key** (starts with `pk_test_` or `pk_live_`)
4. Note your **Secret Key** (starts with `sk_test_` or `sk_live_`)
5. In Clerk Dashboard → JWT Templates, create a new template or use the default
6. Enable Email/Password authentication (or other providers as desired)

## Step 2: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project (or use existing project ID: `llm-council-32883946-c7fc0`)
3. Enable Firestore Database:
   - Go to Firestore Database
   - Click "Create database"
   - Choose "Production mode" or "Test mode" (we have custom rules)
   - Select a region (e.g., `us-central1`)
4. Get your Firebase configuration:
   - Go to Project Settings → General
   - Scroll down to "Your apps"
   - Click the web icon (`</>`) to add a web app
   - Copy the `firebaseConfig` object values

## Step 3: Get OpenRouter API Key

1. Go to [openrouter.ai](https://openrouter.ai/)
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Purchase credits or set up auto-topup
6. Copy your API key (starts with `sk-or-v1-`)

## Step 4: Configure Frontend Environment

Create `frontend/.env` with the following:

```env
# Clerk Authentication
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_key_here

# Firebase Configuration
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=llm-council-32883946-c7fc0.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=llm-council-32883946-c7fc0
VITE_FIREBASE_STORAGE_BUCKET=llm-council-32883946-c7fc0.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

Replace the placeholders with your actual values from Step 2.

## Step 5: Set Firebase Secrets

Firebase Functions use secrets for sensitive data. Set these up:

```bash
# Login to Firebase
firebase login

# Set the OpenRouter API key secret
firebase functions:secrets:set OPENROUTER_API_KEY
# When prompted, paste your OpenRouter API key

# Set the Clerk secret key
firebase functions:secrets:set CLERK_SECRET_KEY
# When prompted, paste your Clerk secret key
```

## Step 6: Configure Firebase Remote Config (Optional)

The council models can be configured via Firebase Remote Config:

1. Go to Firebase Console → Remote Config
2. Add these parameters:
   - `council_models`: Comma-separated list of model IDs
     - Default: `anthropic/claude-3.5-sonnet,google/gemini-pro-1.5,openai/gpt-4o`
   - `chairman_model`: Single model ID for final synthesis
     - Default: `google/gemini-1.5-flash`

Or edit `functions/config.py` to change the default models.

## Step 7: Install Dependencies

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

**Backend (Firebase Functions):**
Dependencies are automatically installed during deployment.

## Step 8: Deploy to Firebase

**Deploy Everything (Hosting + Functions + Firestore Rules):**
```bash
firebase deploy
```

**Or deploy individually:**
```bash
# Deploy only functions
firebase deploy --only functions

# Deploy only hosting
firebase deploy --only hosting

# Deploy only Firestore rules
firebase deploy --only firestore:rules
```

## Step 9: Update Clerk Allowed Origins

After deployment, add your Firebase Hosting URL to Clerk:

1. Go to Clerk Dashboard → Domains
2. Add your Firebase Hosting URL:
   - `https://llm-council-32883946-c7fc0.web.app`
   - `https://llm-council-32883946-c7fc0.firebaseapp.com`

## Step 10: Test the Application

1. Open your Firebase Hosting URL in a browser
2. You should see the Clerk sign-in page
3. Sign up or sign in
4. Try sending a message to the council
5. Verify all 3 stages appear (individual responses, peer reviews, final synthesis)

## Local Development

**Terminal 1 - Firebase Functions Emulator:**
```bash
firebase emulators:start --only functions,firestore
```

**Terminal 2 - Frontend Dev Server:**
```bash
cd frontend
npm run dev
```

**Local Environment:**
- Frontend: http://localhost:5173
- Functions: http://localhost:5001
- Firestore Emulator: http://localhost:8080

For local development, update `frontend/.env` to point to emulators:
```env
VITE_API_URL=http://localhost:5001/llm-council-32883946-c7fc0/us-central1
```

## Architecture Overview

```
┌─────────────┐
│   Browser   │
│  (React)    │
└──────┬──────┘
       │
       │ Clerk JWT Token
       ▼
┌──────────────────┐
│ Firebase Hosting │
│  (Static Files)  │
└──────┬───────────┘
       │
       │ /api/** → Firebase Functions
       ▼
┌──────────────────┐
│ Firebase         │
│ Functions        │◄───── Verify Clerk JWT
│ (on_message)     │
└──────┬───────────┘
       │
       ├────► OpenRouter API (3-stage council)
       │
       └────► Firestore (save conversations)
```

## Firestore Data Structure

```
conversations/{conversationId}
├── userId: string
├── createdAt: timestamp
└── messages/{messageId}
    ├── role: "user" | "assistant"
    ├── content: string (for user messages)
    ├── stage1: array (for assistant messages)
    ├── stage2: array (for assistant messages)
    ├── stage3: object (for assistant messages)
    └── createdAt: timestamp
```

## Security Notes

⚠️ **Important:** The current Firestore rules allow open reads for development purposes. For production:

**Option 1: Integrate Clerk with Firebase Auth**
- Use Clerk's Firebase integration to generate custom tokens
- Update Firestore rules to use `request.auth`

**Option 2: Proxy all reads through Functions**
- Create new Cloud Functions for `getConversations` and `getMessages`
- Verify Clerk JWT in those functions
- Update frontend to call functions instead of Firestore directly

## Costs & Quotas

**Firebase (Spark Plan - Free Tier):**
- Hosting: 10 GB/month
- Functions: 125K invocations/month
- Firestore: 50K reads, 20K writes/day

**OpenRouter:**
- Pay-per-use based on models selected
- Typical cost: $0.01-$0.10 per query (varies by model)

**Clerk:**
- Free tier: 10,000 monthly active users
- All authentication features included

## Troubleshooting

**"Missing VITE_CLERK_PUBLISHABLE_KEY" error:**
- Ensure `frontend/.env` exists with the correct key
- Restart the dev server after creating/updating `.env`

**"Unauthorized" errors:**
- Check that Firebase secrets are set (`firebase functions:secrets:list`)
- Verify Clerk secret key is correct
- Check browser console for JWT verification errors

**"CORS" errors:**
- Ensure Clerk allowed origins include your domain
- Check Firebase Functions CORS headers in `functions/main.py`

**Functions deployment fails:**
- Run `firebase deploy --only functions --debug` for detailed logs
- Verify all secrets are set
- Check Python dependencies in `functions/requirements.txt`

**Firestore permission errors:**
- Run `firebase deploy --only firestore:rules`
- Check rules match the structure in `firestore.rules`

## Model Configuration

Edit `functions/config.py` to customize models:

```python
DEFAULT_COUNCIL_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "google/gemini-pro-1.5",
    "openai/gpt-4o",
    "x-ai/grok-3-mini",  # Add more models
]

DEFAULT_CHAIRMAN_MODEL = "google/gemini-1.5-flash"
```

Or use Firebase Remote Config to change models without redeploying.

## Support

For issues:
- Check Firebase Console → Functions → Logs for backend errors
- Check browser DevTools console for frontend errors
- Review Clerk Dashboard → Logs for authentication issues
- Check OpenRouter Dashboard → Logs for API errors

## Next Steps

- [ ] Set up monitoring and alerts in Firebase Console
- [ ] Configure budget alerts for OpenRouter
- [ ] Implement proper Clerk + Firebase Auth integration
- [ ] Add conversation titles and search
- [ ] Add export functionality
- [ ] Implement real-time message updates
