"""Format Council responses into Slack messages"""

from typing import List, Dict, Any
from .slack_config import PERSONA_EMOJIS, PERSONA_COLORS


def format_stage1_message(stage1_responses: List[Dict[str, Any]]) -> str:
    """Format Stage 1 responses for Slack"""
    blocks = []

    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*Stage 1️⃣: Initial Responses from CTO Council*"
        }
    })

    blocks.append({
        "type": "divider"
    })

    for response in stage1_responses:
        model = response.get("model", "Unknown")
        content = response.get("content", "")

        # Determine persona from model name
        persona_name = model.split("/")[-1]
        emoji = PERSONA_EMOJIS.get(persona_name, "🤖")
        color = PERSONA_COLORS.get(persona_name, "#808080")

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{emoji} *{persona_name}* ({model})\n```{content[:500]}{'...' if len(content) > 500 else ''}```"
            }
        })

    return blocks


def format_stage2_message(
    stage2_rankings: List[Dict[str, Any]],
    label_to_model: Dict[str, str],
    aggregate_rankings: List[Dict[str, Any]]
) -> str:
    """Format Stage 2 rankings for Slack"""
    blocks = []

    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*Stage 2️⃣: Peer Evaluation & Rankings*"
        }
    })

    blocks.append({
        "type": "divider"
    })

    # Show each evaluator's rankings
    for ranking in stage2_rankings:
        model = ranking.get("model", "Unknown")
        parsed = ranking.get("parsed_ranking", [])

        persona_name = model.split("/")[-1]
        emoji = PERSONA_EMOJIS.get(persona_name, "🤖")

        # Format rankings as numbered list
        ranking_text = f"{emoji} *{persona_name}'s Rankings:*\n"
        for i, label in enumerate(parsed, 1):
            model_name = label_to_model.get(label, label)
            ranking_text += f"{i}. {label} ({model_name})\n"

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ranking_text
            }
        })

    # Show aggregate rankings
    blocks.append({
        "type": "divider"
    })

    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*Aggregate Rankings (Average Position):*"
        }
    })

    for agg in aggregate_rankings:
        model = agg.get("model", "Unknown")
        score = agg.get("average_score", 0)
        votes = agg.get("votes", 0)

        persona_name = model.split("/")[-1]
        emoji = PERSONA_EMOJIS.get(persona_name, "🤖")

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{emoji} *{persona_name}*: {score} (from {votes} evaluations)"
            }
        })

    return blocks


def format_stage3_message(stage3_response: Dict[str, Any]) -> str:
    """Format Stage 3 final answer for Slack"""
    blocks = []

    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*Stage 3️⃣: Final Synthesized Answer*"
        }
    })

    blocks.append({
        "type": "divider"
    })

    content = stage3_response.get("content", "No response generated")

    # Split into chunks if too long
    if len(content) > 3000:
        chunks = [content[i:i+3000] for i in range(0, len(content), 3000)]
        for chunk in chunks:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": chunk
                }
            })
    else:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": content
            }
        })

    return blocks


def format_thinking_message() -> Dict[str, Any]:
    """Format loading/thinking message"""
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "⏳ *CTO Council is deliberating...*\nThis may take 1-2 minutes as the council members respond, evaluate each other, and synthesize the final answer."
        }
    }
