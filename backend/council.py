"""LLM Council - 3-stage deliberation system."""

import random
import re
from typing import List, Dict, Tuple, Any

from .openrouter import query_models_parallel


async def stage1_collect_responses(
    models: List[str],
    prompt: str,
    api_key: str
) -> List[Dict[str, Any]]:
    """Stage 1: Query all council models in parallel for initial responses."""
    print(f"Stage 1: Querying {len(models)} council members...")
    responses = await query_models_parallel(models, prompt, api_key)
    print(f"Stage 1: Received {len(responses)} responses")
    return responses


async def stage2_collect_rankings(
    stage1_responses: List[Dict[str, Any]],
    question: str,
    api_key: str,
    council_models: List[str]
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """Stage 2: Anonymize responses and ask models to rank their peers."""
    if not stage1_responses:
        return [], {}

    print(f"Stage 2: Collecting peer evaluations from {len(council_models)} evaluators...")

    # Anonymize responses to prevent bias
    shuffled_responses = random.sample(stage1_responses, len(stage1_responses))
    label_to_model = {
        f"Response {chr(65 + i)}": resp["model"]
        for i, resp in enumerate(shuffled_responses)
    }
    anonymized_responses_text = "\n\n".join([
        f'{label}:\n{resp["content"]}'
        for label, resp in zip(label_to_model.keys(), shuffled_responses)
    ])

    # Construct evaluation prompt
    ranking_prompt = (
        f"You are a member of an LLM council tasked with evaluating responses to a user's question. "
        f"The user's original question was: \"{question}\".\n\n"
        f"Here are the anonymized responses from your fellow council members:\n\n"
        f"{anonymized_responses_text}\n\n"
        f"Your task is to act as an impartial judge. Please evaluate the quality of each response "
        f"based on accuracy, clarity, and insight. Provide a brief evaluation for each response, "
        f"and then provide a final ranking in a specific format.\n\n"
        f"Instructions:\n"
        f"1. Write a short critique for each response (e.g., \"Response A is good but misses a key point...\").\n"
        f"2. After your evaluations, you MUST include a section that starts with the header 'FINAL RANKING:'.\n"
        f"3. In this section, list the responses in order from best to worst. "
        f"For example: \"1. Response C\", \"2. Response A\", \"3. Response B\".\n"
        f"4. Do not add any text after the final ranking list."
    )

    # Query all models for rankings
    ranking_responses = await query_models_parallel(council_models, ranking_prompt, api_key)

    # Parse rankings from responses
    parsed_rankings = []
    for ranking_resp in ranking_responses:
        if ranking_resp and ranking_resp.get('content'):
            parsed, raw_text = parse_ranking_from_text(
                ranking_resp['content'],
                list(label_to_model.keys())
            )
            parsed_rankings.append({
                "model": ranking_resp["model"],
                "evaluation_text": raw_text,
                "parsed_ranking": parsed
            })

    print(f"Stage 2: Parsed {len(parsed_rankings)} evaluations")
    return parsed_rankings, label_to_model


def parse_ranking_from_text(text: str, labels: List[str]) -> Tuple[List[str], str]:
    """Extract ordered list of ranked responses from evaluation text."""
    try:
        # Find content after "FINAL RANKING:"
        ranking_section = re.search(r"FINAL RANKING:(.*)", text, re.DOTALL | re.IGNORECASE)
        if not ranking_section:
            # Fallback: find any ordered list of labels
            return _extract_labels_in_order(text, labels), text

        ranking_text = ranking_section.group(1).strip()
        ranked_labels = _extract_labels_in_order(ranking_text, labels)
        return ranked_labels, text
    except Exception as e:
        print(f"Error parsing ranking text: {e}")
        return [], text


def _extract_labels_in_order(text: str, labels: List[str]) -> List[str]:
    """Find all label occurrences in text and return them in order."""
    pattern = "(" + "|".join(re.escape(label) for label in labels) + ")"
    return re.findall(pattern, text)


async def stage3_synthesize_final(
    stage1_responses: List[Dict[str, Any]],
    stage2_rankings: List[Dict[str, Any]],
    question: str,
    api_key: str,
    chairman_model: str
) -> Dict[str, Any]:
    """Stage 3: Chairman model synthesizes final answer based on all inputs."""
    if not stage1_responses:
        return {"content": "I am sorry, but I was unable to generate a response."}

    print("Stage 3: Synthesizing final answer...")

    # Prepare context for chairman
    s1_text = "\n\n".join([
        f'{resp["model"]}:\n{resp["content"]}'
        for resp in stage1_responses
    ])
    s2_text = "\n\n".join([
        f'Evaluator: {ranking["model"]}\nCritique: {ranking["evaluation_text"]}'
        for ranking in stage2_rankings
    ])

    synthesis_prompt = (
        f"You are the Chairman of an LLM council. Your task is to synthesize a final, "
        f"high-quality answer to a user's question based on the submissions and peer reviews "
        f"from the council members.\n\n"
        f"The user's original question was: \"{question}\".\n\n"
        f"--- STAGE 1: Initial Responses ---\n"
        f"Here are the initial responses from the council members:\n\n{s1_text}\n\n"
        f"--- STAGE 2: Peer Evaluations ---\n"
        f"Here are the peer evaluations of those responses:\n\n{s2_text}\n\n"
        f"--- Your Task ---\n"
        f"Synthesize all of this information into a single, comprehensive, and well-written "
        f"final answer for the user. Your answer should be the definitive response, drawing on "
        f"the strengths of the best submissions and correcting any identified flaws. "
        f"Do not refer to the stages or the council directly in your final output. "
        f"Simply provide the best possible answer to the user's question."
    )

    # Query chairman model
    final_response = await query_models_parallel([chairman_model], synthesis_prompt, api_key)
    if final_response:
        print("Stage 3: Final answer synthesized")
        return final_response[0]
    else:
        return {"content": "The chairman failed to generate a response."}


def calculate_aggregate_rankings(
    stage2_rankings: List[Dict[str, Any]],
    label_to_model: Dict[str, str]
) -> List[Dict[str, Any]]:
    """Calculate aggregate ranking for each model based on peer evaluations."""
    if not stage2_rankings:
        return []

    # Initialize scores for each model
    model_scores = {
        model: {"total_score": 0, "votes": 0}
        for model in label_to_model.values()
    }

    # Accumulate scores from all rankings
    for ranking in stage2_rankings:
        ranked_labels = ranking.get("parsed_ranking", [])
        for i, label in enumerate(ranked_labels):
            # Score based on position (last place = 1 point, first = num_responses points)
            score = len(ranked_labels) - i
            model_name = label_to_model.get(label)
            if model_name:
                model_scores[model_name]["total_score"] += score
                model_scores[model_name]["votes"] += 1

    # Calculate averages and sort
    aggregate_rankings = []
    for model, data in model_scores.items():
        if data["votes"] > 0:
            average_score = data["total_score"] / data["votes"]
            aggregate_rankings.append({
                "model": model,
                "average_score": round(average_score, 2),
                "votes": data["votes"]
            })

    return sorted(aggregate_rankings, key=lambda x: x["average_score"], reverse=True)


async def generate_conversation_title(prompt: str, api_key: str) -> str:
    """Generate a brief title for the conversation."""
    title_prompt = (
        f"Generate a very brief (5-8 words) title for a conversation that starts with: \"{prompt[:100]}...\"\n\n"
        f"Just the title, nothing else."
    )
    responses = await query_models_parallel(["anthropic/claude-sonnet-4-5"], title_prompt, api_key)
    if responses:
        return responses[0].get("content", "New Conversation").strip()
    return "New Conversation"


async def run_full_council(
    prompt: str,
    api_key: str,
    council_models: List[str],
    chairman_model: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any], Dict[str, Any]]:
    """Execute full 3-stage council process."""
    try:
        # Stage 1
        stage1_responses = await stage1_collect_responses(council_models, prompt, api_key)
        if not stage1_responses:
            raise ValueError("No responses from Stage 1")

        # Stage 2
        stage2_rankings, label_to_model = await stage2_collect_rankings(
            stage1_responses, prompt, api_key, council_models
        )

        # Stage 3
        stage3_response = await stage3_synthesize_final(
            stage1_responses, stage2_rankings, prompt, api_key, chairman_model
        )

        # Calculate metadata
        aggregate_rankings = calculate_aggregate_rankings(stage2_rankings, label_to_model)
        metadata = {
            "label_to_model": label_to_model,
            "aggregate_rankings": aggregate_rankings
        }

        return stage1_responses, stage2_rankings, stage3_response, metadata

    except Exception as e:
        print(f"Error in council process: {e}")
        raise
