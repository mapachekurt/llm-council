import json
import asyncio
from datetime import datetime
from firebase_admin import firestore
from firebase_functions import https_fn

# Import the configuration and core logic
from . import config
from . import council

# Get a reference to the Firestore database
db = firestore.client()

@https_fn.on_request(secrets=[config.OPENROUTER_API_KEY])
def on_message(req: https_fn.Request) -> https_fn.Response:
    """Firebase Function to handle a new message in a conversation."""
    # Set CORS headers for preflight and actual requests
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    }

    if req.method == "OPTIONS":
        return https_fn.Response("", headers=headers)

    if req.method != "POST":
        return https_fn.Response("Method Not Allowed", status=405, headers=headers)

    try:
        # Extract conversation ID from the URL path, e.g., /on_message/12345
        path_parts = req.path.split('/')
        if len(path_parts) < 2 or not path_parts[-1]:
            return https_fn.Response("Missing conversation ID.", status=400, headers=headers)
        conversation_id = path_parts[-1]

        # Get the user's prompt from the request body
        data = req.get_json()
        user_prompt = data.get("prompt")
        if not user_prompt:
            return https_fn.Response("Missing 'prompt' in request body.", status=400, headers=headers)

        # Retrieve the OpenRouter API key from the secrets
        api_key = config.OPENROUTER_API_KEY.value

        # --- Execute the 3-Stage Council Process (async) ---
        print(f"Executing 3-stage council process for conversation {conversation_id}...")
        stage1_responses, stage2_rankings, label_to_model, stage3_response = asyncio.run(
            run_full_council_async(user_prompt, api_key)
        )

        # --- Calculate Aggregate Rankings for Metadata ---
        aggregate_rankings = council.calculate_aggregate_rankings(stage2_rankings, label_to_model)

        # --- Persist to Firestore ---
        print("Persisting results to Firestore...")
        conversation_ref = db.collection("conversations").document(conversation_id)

        # Use a batch write for atomicity
        batch = db.batch()

        # Set conversation creation timestamp if it's a new conversation
        batch.set(conversation_ref, {"createdAt": firestore.SERVER_TIMESTAMP}, merge=True)

        # Save the user's message
        user_msg_ref = conversation_ref.collection("messages").document()
        batch.set(user_msg_ref, {
            "role": "user",
            "content": user_prompt,
            "createdAt": firestore.SERVER_TIMESTAMP
        })

        # Save the assistant's multi-stage response
        assistant_msg_ref = conversation_ref.collection("messages").document()
        batch.set(assistant_msg_ref, {
            "role": "assistant",
            "createdAt": firestore.SERVER_TIMESTAMP,
            "stage1": stage1_responses,
            "stage2": stage2_rankings,
            "stage3": stage3_response,
        })

        batch.commit()
        print("Successfully saved to Firestore.")

        # --- Prepare the API Response ---
        response_data = {
            "id": assistant_msg_ref.id,
            "role": "assistant",
            "stage1": stage1_responses,
            "stage2": stage2_rankings,
            "stage3": stage3_response,
            "metadata": {
                "label_to_model": label_to_model,
                "aggregate_rankings": aggregate_rankings
            }
        }

        return https_fn.Response(json.dumps(response_data, default=str), status=200, headers=headers, mimetype="application/json")

    except Exception as e:
        print(f"Error processing request: {e}")
        import traceback
        traceback.print_exc()
        return https_fn.Response(f"Internal Server Error: {e}", status=500, headers=headers)


async def run_full_council_async(user_prompt: str, api_key: str):
    """Execute the full 3-stage council process asynchronously."""
    try:
        # Stage 1: Collect responses
        print("Stage 1: Collecting responses from council members...")
        stage1_responses = await council.stage1_collect_responses(
            config.COUNCIL_MODELS, user_prompt, api_key
        )

        if not stage1_responses:
            raise ValueError("No responses received from council members in Stage 1")

        # Stage 2: Collect rankings
        print("Stage 2: Collecting peer evaluations...")
        stage2_rankings, label_to_model = await council.stage2_collect_rankings(
            stage1_responses, user_prompt, api_key, config.COUNCIL_MODELS
        )

        # Stage 3: Synthesize final answer
        print("Stage 3: Synthesizing final answer...")
        stage3_response = await council.stage3_synthesize_final(
            stage1_responses, stage2_rankings, user_prompt, api_key, config.CHAIRMAN_MODEL
        )

        return stage1_responses, stage2_rankings, label_to_model, stage3_response

    except Exception as e:
        print(f"Error in council process: {e}")
        raise
