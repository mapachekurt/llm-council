"""Handle Slack events and manage bot interaction"""

import asyncio
import json
import hmac
import hashlib
import time
from typing import Dict, Any, Optional
import httpx

from . import storage_firestore
from . import council
from . import config
from .slack_config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, SLACK_API_BASE
from .slack_formatter import (
    format_stage1_message,
    format_stage2_message,
    format_stage3_message,
    format_thinking_message,
)


class SlackHandler:
    """Manages Slack bot interactions and message posting"""

    def __init__(self):
        self.bot_token = SLACK_BOT_TOKEN
        self.signing_secret = SLACK_SIGNING_SECRET

    def verify_slack_signature(self, timestamp: str, signature: str, body: str) -> bool:
        """Verify that the request came from Slack"""
        if abs(time.time() - int(timestamp)) > 300:
            return False  # Request too old

        sig_basestring = f"v0:{timestamp}:{body}"
        my_signature = (
            "v0="
            + hmac.new(
                self.signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256,
            ).hexdigest()
        )

        return hmac.compare_digest(my_signature, signature)

    async def handle_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Slack event"""
        event = payload.get("event", {})
        event_type = event.get("type")

        if event_type == "message":
            return await self.handle_message(event)
        elif payload.get("type") == "url_verification":
            return {"challenge": payload.get("challenge")}

        return {"ok": True}

    async def handle_message(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming Slack message"""
        user_id = event.get("user")
        channel_id = event.get("channel")
        text = event.get("text", "").strip()
        thread_ts = event.get("thread_ts")
        message_ts = event.get("ts")

        # Ignore bot messages and empty messages
        if not text or event.get("bot_id"):
            return {"ok": True}

        # Ignore messages in threads (only respond to main messages)
        if thread_ts:
            return {"ok": True}

        try:
            # Create conversation in Firestore
            conversation_id = f"slack_{channel_id}_{message_ts}"
            storage_firestore.create_conversation(conversation_id)

            # Post thinking message
            thinking_blocks = [format_thinking_message()]
            response = await self.post_message(
                channel_id, thinking_blocks, metadata={"event_type": "pending"}
            )
            thinking_ts = response.get("ts")

            # Run the council process
            stage1, stage2, stage3, metadata = await council.run_full_council(
                text, config.OPENROUTER_API_KEY, config.COUNCIL_MODELS, config.CHAIRMAN_MODEL
            )

            # Save to Firestore
            storage_firestore.add_user_message(conversation_id, text)
            storage_firestore.add_assistant_message(
                conversation_id, stage1, stage2, stage3
            )

            # Post Stage 1 in thread
            stage1_blocks = format_stage1_message(stage1)
            await self.post_message(
                channel_id,
                stage1_blocks,
                thread_ts=thinking_ts,
                metadata={"stage": "1"},
            )

            # Post Stage 2 in thread
            stage2_blocks = format_stage2_message(
                stage2,
                metadata.get("label_to_model", {}),
                metadata.get("aggregate_rankings", []),
            )
            await self.post_message(
                channel_id,
                stage2_blocks,
                thread_ts=thinking_ts,
                metadata={"stage": "2"},
            )

            # Post Stage 3 in thread
            stage3_blocks = format_stage3_message(stage3)
            await self.post_message(
                channel_id,
                stage3_blocks,
                thread_ts=thinking_ts,
                metadata={"stage": "3"},
            )

            return {"ok": True}

        except Exception as e:
            print(f"Error handling Slack message: {e}")
            await self.post_message(
                channel_id,
                [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"❌ *Error:* {str(e)}\n\nThe CTO Council encountered an issue processing your question.",
                        },
                    }
                ],
                thread_ts=message_ts,
            )
            return {"ok": False, "error": str(e)}

    async def post_message(
        self,
        channel_id: str,
        blocks: list,
        thread_ts: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Post a message to Slack"""
        async with httpx.AsyncClient() as client:
            payload = {
                "channel": channel_id,
                "blocks": blocks,
            }

            if thread_ts:
                payload["thread_ts"] = thread_ts

            if metadata:
                payload["metadata"] = {
                    "event_type": "council_response",
                    "event_payload": metadata,
                }

            response = await client.post(
                f"{SLACK_API_BASE}/chat.postMessage",
                json=payload,
                headers={"Authorization": f"Bearer {self.bot_token}"},
            )

            return response.json()

    async def update_message(
        self,
        channel_id: str,
        ts: str,
        blocks: list,
    ) -> Dict[str, Any]:
        """Update an existing Slack message"""
        async with httpx.AsyncClient() as client:
            payload = {
                "channel": channel_id,
                "ts": ts,
                "blocks": blocks,
            }

            response = await client.post(
                f"{SLACK_API_BASE}/chat.update",
                json=payload,
                headers={"Authorization": f"Bearer {self.bot_token}"},
            )

            return response.json()


# Global handler instance
slack_handler = SlackHandler()
