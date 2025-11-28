import os
from firebase_admin import initialize_app, remoteconfig
from firebase_functions import options

# It'''s recommended to set the project ID in the environment
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

# --- Model Configuration ---
# You can manage your model lists in Firebase Remote Config for easy updates
# without redeploying your function.

# Initialize Remote Config
remote_config_client = remoteconfig.Client()

# Get the template
try:
    template = remote_config_client.get_template()
except Exception as e:
    print(f"Could not fetch remote config template, using defaults: {e}")
    template = remoteconfig.RemoteConfigTemplate()


# Define default model lists
DEFAULT_COUNCIL_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "google/gemini-pro-1.5",
    "openai/gpt-4o",
]
DEFAULT_CHAIRMAN_MODEL = "google/gemini-1.5-flash"

# Set default parameters in the template if they don'''t exist
if "council_models" not in template.parameters:
    template.parameters["council_models"] = remoteconfig.Parameter(
        default_value={"value": ",".join(DEFAULT_COUNCIL_MODELS)},
        description="Comma-separated list of OpenRouter model identifiers for the council.",
        value_type=remoteconfig.ParameterValueType.STRING
    )
if "chairman_model" not in template.parameters:
    template.parameters["chairman_model"] = remoteconfig.Parameter(
        default_value={"value": DEFAULT_CHAIRMAN_MODEL},
        description="The model identifier for the chairman.",
        value_type=remoteconfig.ParameterValueType.STRING
    )

# Publish the template with default values if it was modified
# In a real-world scenario, you might do this once via a setup script
# or through the Firebase Console. For this example, we ensure it'''s set.
try:
    remote_config_client.publish_template(template)
    print("Successfully published remote config template.")
except Exception as e:
    print(f"Could not publish remote config template, using defaults: {e}")

# Fetch the latest config
remote_config_client.fetch_config()

# Get council models and chairman model from Remote Config
COUNCIL_MODELS = remote_config_client.get_config().get("council_models").as_string().split(',')
CHAIRMAN_MODEL = remote_config_client.get_config().get("chairman_model").as_string()

# Fallback to defaults if the config is empty
if not COUNCIL_MODELS or (len(COUNCIL_MODELS) == 1 and not COUNCIL_MODELS[0]):
    COUNCIL_MODELS = DEFAULT_COUNCIL_MODELS
if not CHAIRMAN_MODEL:
    CHAIRMAN_MODEL = DEFAULT_CHAIRMAN_MODEL

# --- API Key Configuration ---
# Get the OpenRouter API key from Firebase Functions secrets
# To set this, run:
# firebase functions:secrets:set OPENROUTER_API_KEY
# You will be prompted to enter the secret value.
OPENROUTER_API_KEY = options.SecretOption("OPENROUTER_API_KEY")

print("--- Configuration Loaded ---")
print(f"Project ID: {project_id}")
print(f"Council Models: {COUNCIL_MODELS}")
print(f"Chairman Model: {CHAIRMAN_MODEL}")
print("--------------------------")
