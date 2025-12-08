"""Configuration for LLM Council backend."""

import os
from pathlib import Path

# --- Project Paths ---
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data" / "conversations"

# --- CTO Council Configuration ---
# The LLM Council uses CTO personas for specialized technical perspectives

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

# --- API Configuration ---
# Get OpenRouter API key from environment
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# --- Server Configuration ---
HOST = "0.0.0.0"
PORT = 8001

# --- Firestore Configuration ---
# For local development: ensure FIRESTORE_EMULATOR_HOST is set if using emulator
FIRESTORE_EMULATOR_HOST = os.getenv("FIRESTORE_EMULATOR_HOST", None)
USE_FIRESTORE = os.getenv("USE_FIRESTORE", "true").lower() == "true"
