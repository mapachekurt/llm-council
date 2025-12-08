"""Firestore-based storage for conversations."""

from datetime import datetime
from typing import List, Dict, Any, Optional

from firebase_admin import firestore, initialize_app, credentials
import os


# Initialize Firebase Admin SDK
try:
    # Try to use application default credentials (set by GOOGLE_APPLICATION_CREDENTIALS)
    initialize_app()
except Exception as e:
    print(f"Warning: Could not initialize Firebase app: {e}")
    # This is OK for local development where we might be using the emulator


def get_db():
    """Get Firestore database client."""
    try:
        return firestore.client()
    except Exception as e:
        print(f"Error getting Firestore client: {e}")
        raise


def create_conversation(conversation_id: str) -> Dict[str, Any]:
    """Create a new conversation in Firestore."""
    db = get_db()
    conversation = {
        "id": conversation_id,
        "created_at": datetime.utcnow().isoformat(),
        "title": "New Conversation",
        "messages": []
    }

    # Create conversation document
    db.collection("conversations").document(conversation_id).set({
        "created_at": firestore.SERVER_TIMESTAMP,
        "title": "New Conversation",
        "message_count": 0
    })

    return conversation


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a conversation from Firestore."""
    db = get_db()

    try:
        doc = db.collection("conversations").document(conversation_id).get()

        if not doc.exists:
            return None

        conv_data = doc.to_dict()

        # Get all messages in the conversation
        messages = []
        messages_ref = db.collection("conversations").document(conversation_id).collection("messages")
        for msg_doc in messages_ref.order_by("created_at").stream():
            msg = msg_doc.to_dict()
            msg["id"] = msg_doc.id
            messages.append(msg)

        return {
            "id": conversation_id,
            "created_at": conv_data.get("created_at", ""),
            "title": conv_data.get("title", "New Conversation"),
            "messages": messages
        }

    except Exception as e:
        print(f"Error retrieving conversation {conversation_id}: {e}")
        return None


def list_conversations(limit: int = 50) -> List[Dict[str, Any]]:
    """List all conversations (metadata only)."""
    db = get_db()

    try:
        conversations = []
        docs = db.collection("conversations").order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit).stream()

        for doc in docs:
            data = doc.to_dict()
            # Count messages in this conversation
            messages_count = 0
            try:
                messages_ref = db.collection("conversations").document(doc.id).collection("messages")
                messages_count = len(list(messages_ref.stream()))
            except Exception:
                pass

            conversations.append({
                "id": doc.id,
                "created_at": data.get("created_at", ""),
                "title": data.get("title", "New Conversation"),
                "message_count": messages_count
            })

        return conversations

    except Exception as e:
        print(f"Error listing conversations: {e}")
        return []


def add_user_message(conversation_id: str, content: str) -> bool:
    """Add a user message to a conversation."""
    db = get_db()

    try:
        messages_ref = db.collection("conversations").document(conversation_id).collection("messages")
        messages_ref.add({
            "role": "user",
            "content": content,
            "created_at": firestore.SERVER_TIMESTAMP
        })

        # Update message count
        db.collection("conversations").document(conversation_id).update({
            "message_count": firestore.Increment(1)
        })

        return True

    except Exception as e:
        print(f"Error adding user message: {e}")
        return False


def add_assistant_message(
    conversation_id: str,
    stage1: List[Dict[str, Any]],
    stage2: List[Dict[str, Any]],
    stage3: Dict[str, Any]
) -> bool:
    """Add an assistant message with all 3 stages to a conversation."""
    db = get_db()

    try:
        messages_ref = db.collection("conversations").document(conversation_id).collection("messages")
        messages_ref.add({
            "role": "assistant",
            "stage1": stage1,
            "stage2": stage2,
            "stage3": stage3,
            "created_at": firestore.SERVER_TIMESTAMP
        })

        # Update message count
        db.collection("conversations").document(conversation_id).update({
            "message_count": firestore.Increment(1)
        })

        return True

    except Exception as e:
        print(f"Error adding assistant message: {e}")
        return False


def update_conversation_title(conversation_id: str, title: str) -> bool:
    """Update the title of a conversation."""
    db = get_db()

    try:
        db.collection("conversations").document(conversation_id).update({
            "title": title
        })
        return True

    except Exception as e:
        print(f"Error updating conversation title: {e}")
        return False


def save_conversation_metadata(conversation_id: str, metadata: Dict[str, Any]) -> bool:
    """Save metadata for a conversation (e.g., aggregate rankings, label mappings)."""
    db = get_db()

    try:
        db.collection("conversations").document(conversation_id).update({
            "metadata": metadata
        })
        return True

    except Exception as e:
        print(f"Error saving conversation metadata: {e}")
        return False


def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation and all its messages."""
    db = get_db()

    try:
        # Delete all messages in the conversation
        messages_ref = db.collection("conversations").document(conversation_id).collection("messages")
        for doc in messages_ref.stream():
            doc.reference.delete()

        # Delete the conversation document
        db.collection("conversations").document(conversation_id).delete()
        return True

    except Exception as e:
        print(f"Error deleting conversation: {e}")
        return False
