import os
from firebase_admin import initialize_app
from firebase_functions import options

# It's recommended to set the project ID in the environment
# for both local development and deployed functions.
# For local dev, use:
# export GCLOUD_PROJECT=your-project-id
# For deployed functions, this is set automatically.
project_id = os.environ.get('GCLOUD_PROJECT')
if not project_id:
    raise ValueError("GCLOUD_PROJECT environment variable not set.")

# Set the region for all functions in this file
options.set_global_options(region="us-central1")

# Initialize Firebase Admin SDK
try:
    app = initialize_app()
except ValueError:
    # If initialize_app() is called more than once, it raises a ValueError.
    # This can happen during hot reloads in a local development environment.
    # We can safely ignore this error.
    pass

# --- CTO Council Configuration ---
# The LLM Council now uses CTO personas for specialized technical perspectives

# CTO Personas - each brings unique expertise
COUNCIL_MEMBERS = [
    {
        "id": "cto-orchestrator",
        "model": "anthropic/claude-sonnet-4-5",
        "color": "blue",
        "role": "Orchestrator",
        "description": "Clarifies ambiguous requests and defines clear scope"
    },
    {
        "id": "cto-architect",
        "model": "anthropic/claude-opus-4-1",
        "color": "green",
        "role": "Architect",
        "description": "System design with trade-offs and scalability"
    },
    {
        "id": "cto-mentor",
        "model": "anthropic/claude-opus-4-1",
        "color": "red",
        "role": "Mentor",
        "description": "Ruthless feedback and critical verdicts"
    },
    {
        "id": "cto-visionary",
        "model": "google/gemini-3-pro",
        "color": "purple",
        "role": "Visionary",
        "description": "Innovation focus and emerging technology trends"
    }
]

# Extract model list for legacy compatibility
COUNCIL_MODELS = [member["model"] for member in COUNCIL_MEMBERS]

# Chairman model - synthesizes perspectives
CHAIRMAN_MODEL = "anthropic/claude-sonnet-4-5"

# --- API Key Configuration ---
# Get the OpenRouter API key from Firebase Functions secrets
# To set this, run:
# firebase functions:secrets:set OPENROUTER_API_KEY
# You will be prompted to enter the secret value.
OPENROUTER_API_KEY = options.SecretOption("OPENROUTER_API_KEY")

print("--- CTO Council Configuration Loaded ---")
print(f"Project ID: {project_id}")
print(f"Council Members: {len(COUNCIL_MEMBERS)}")
for member in COUNCIL_MEMBERS:
    print(f"  - {member['id']}: {member['model']} ({member['role']})")
print(f"Chairman Model: {CHAIRMAN_MODEL}")
print("----------------------------------------")
