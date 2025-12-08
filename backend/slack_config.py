"""Slack Bot Configuration and Credentials"""

import os
from typing import Optional

# Slack workspace and channel info
SLACK_WORKSPACE_ID = "T07B3RRNQ87"
SLACK_CHANNEL_ID = "C07BLSVMP9S"
SLACK_BOT_NAME = "cto council"

# Slack credentials - get from environment variables
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")  # xoxb-...
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")  # For verifying requests

# Slack API endpoints
SLACK_API_BASE = "https://slack.com/api"

# Slack message configuration
SLACK_THREAD_TIMEOUT = 1800  # 30 minutes - how long to keep a thread open

# Stage display configuration
STAGE_DISPLAY = {
    "stage1": {
        "title": "Stage 1: Initial Responses from CTO Council",
        "show_all": True,  # Show all 4 responses
    },
    "stage2": {
        "title": "Stage 2: Peer Evaluation & Rankings",
        "show_evaluations": True,
        "show_parsed_rankings": True,
    },
    "stage3": {
        "title": "Stage 3: Final Synthesized Answer",
        "show_context": False,  # Just the final answer
    },
}

# Color coding for personas
PERSONA_COLORS = {
    "cto-orchestrator": "#4A90E2",  # Blue
    "cto-architect": "#50C878",      # Green
    "cto-mentor": "#E85D75",         # Red
    "cto-visionary": "#9B59B6",      # Purple
}

PERSONA_EMOJIS = {
    "cto-orchestrator": "🔵",
    "cto-architect": "🟢",
    "cto-mentor": "🔴",
    "cto-visionary": "🟣",
}
