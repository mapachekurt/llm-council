import json
from datetime import datetime
from firebase_admin import firestore
from firebase_functions import https_fn

# Import the configuration and core logic
from . import config
from . import council
from . import auth

# Get a reference to the Firestore database
db = firestore.client()

@https_fn.on_request(secrets=[config.OPENROUTER_API_KEY, config.CLERK_SECRET_KEY])
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
        # --- Verify Authentication ---
        auth_header = req.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return https_fn.Response("Unauthorized: Missing or invalid Authorization header", status=401, headers=headers)

        token = auth_header.split(' ')[1]

        try:
            decoded_token = auth.verify_clerk_token(token, config.CLERK_SECRET_KEY.value)
            user_id = auth.extract_user_id(decoded_token)
        except Exception as e:
            print(f"Authentication error: {e}")
            return https_fn.Response(f"Unauthorized: {str(e)}", status=401, headers=headers)

        print(f"Authenticated user: {user_id}")

        # Extract conversation ID from the URL path, e.g., /api/conversations/12345/message
        path_parts = req.path.split('/')
        # Path format: ['', 'api', 'conversations', '{id}', 'message']
        if 'conversations' in path_parts:
            conv_index = path_parts.index('conversations')
            if conv_index + 1 < len(path_parts):
                conversation_id = path_parts[conv_index + 1]
            else:
                return https_fn.Response("Missing conversation ID.", status=400, headers=headers)
        else:
            return https_fn.Response("Invalid API path.", status=400, headers=headers)

        # Get the user'''s prompt from the request body
        data = req.get_json()
        user_prompt = data.get("prompt")
        if not user_prompt:
            return https_fn.Response("Missing 'prompt' in request body.", status=400, headers=headers)

        # Retrieve the OpenRouter API key from the secrets
        api_key = config.OPENROUTER_API_KEY.value

        # --- Execute the 3-Stage Council Process ---
        print(f"Executing Stage 1 for conversation {conversation_id}...")
        stage1_responses = council.stage1_collect_responses(config.COUNCIL_MODELS, user_prompt, api_key)

        print("Executing Stage 2...")
        stage2_rankings, label_to_model, _ = council.stage2_collect_rankings(
            stage1_responses, user_prompt, api_key, config.COUNCIL_MODELS
        )

        print("Executing Stage 3...")
        stage3_response = council.stage3_synthesize_final(
            stage1_responses, stage2_rankings, user_prompt, api_key, config.CHAIRMAN_MODEL
        )

        # --- Calculate Aggregate Rankings for Metadata ---
        aggregate_rankings = council.calculate_aggregate_rankings(stage2_rankings, label_to_model)

        # --- Persist to Firestore ---
        print("Persisting results to Firestore...")
        conversation_ref = db.collection("conversations").document(conversation_id)
        
        # Create a new message document in the 'messages' subcollection
        assistant_message_ref = conversation_ref.collection("messages").document()
        user_message_ref = conversation_ref.collection("messages").document()

        # Use a transaction or batch write for atomicity
        batch = db.batch()

        # Set conversation creation timestamp and user ID if it's a new conversation
        batch.set(conversation_ref, {
            "createdAt": firestore.SERVER_TIMESTAMP,
            "userId": user_id
        }, merge=True)

        # Save the user'''s message
        batch.set(user_message_ref, {
            "role": "user",
            "content": user_prompt,
            "createdAt": firestore.SERVER_TIMESTAMP
        })

        # Save the assistant'''s multi-stage response
        batch.set(assistant_message_ref, {
            "role": "assistant",
            "createdAt": firestore.SERVER_TIMESTAMP,
            "stage1": stage1_responses,
            "stage2": stage2_rankings,
            "stage3": stage3_response,
            # Metadata is not persisted to save space and cost, as per original design.
            # It'''s generated on the fly and returned to the client.
        })

        batch.commit()
        print("Successfully saved to Firestore.")

        # --- Prepare the API Response ---
        response_data = {
            "id": assistant_message_ref.id,
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
