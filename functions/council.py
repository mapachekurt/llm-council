import asyncio
import random
import re
from .openrouter import query_models_parallel

# --- Stage 1: Collect Initial Responses ---
async def stage1_collect_responses(models: list, prompt: str, api_key: str):
    """Async: Queries all council models in parallel for their initial responses."""
    return await query_models_parallel(models, prompt, api_key)

# --- Stage 2: Collect Peer Rankings ---
async def stage2_collect_rankings(stage1_responses: list, question: str, api_key: str, council_models: list):
    """Async: Anonymizes responses and asks each model to rank its peers."""
    if not stage1_responses:
        return [], {}

    # Anonymize the responses into a dictionary of "Response A", "Response B", etc.
    # This prevents models from being biased towards their own output.
    shuffled_responses = random.sample(stage1_responses, len(stage1_responses))
    label_to_model = {f"Response {chr(65 + i)}": resp["model"] for i, resp in enumerate(shuffled_responses)}
    anonymized_responses_text = "\n\n".join([f'{label}:\n{resp["content"]}' for label, resp in zip(label_to_model.keys(), shuffled_responses)])

    # Construct the prompt for evaluation
    ranking_prompt = (
        f"You are a member of an LLM council tasked with evaluating responses to a user's question. "
        f"The user's original question was: \"{question}\".\n\n"
        f"Here are the anonymized responses from your fellow council members:\n\n"
        f"{anonymized_responses_text}\n\n"
        f"Your task is to act as an impartial judge. Please evaluate the quality of each response based on accuracy, clarity, and insight. "
        f"Provide a brief evaluation for each response, and then provide a final ranking in a specific format.\n\n"
        f"Instructions:\n"
        f"1. Write a short critique for each response (e.g., \"Response A is good but misses a key point...\").\n"
        f"2. After your evaluations, you MUST include a section that starts with the header 'FINAL RANKING:'.\n"
        f"3. In this section, list the responses in order from best to worst. For example: \"1. Response C\", \"2. Response A\", \"3. Response B\".\n"
        f"4. Do not add any text after the final ranking list."
    )

    # Query all models again for their rankings
    ranking_responses = await query_models_parallel(council_models, ranking_prompt, api_key)

    # Parse the rankings from the raw text responses
    parsed_rankings = []
    for ranking_resp in ranking_responses:
        if ranking_resp and ranking_resp.get('content'):
            parsed, raw_text = parse_ranking_from_text(ranking_resp['content'], list(label_to_model.keys()))
            parsed_rankings.append({
                "model": ranking_resp["model"],
                "evaluation_text": raw_text,
                "parsed_ranking": parsed
            })

    return parsed_rankings, label_to_model

def parse_ranking_from_text(text: str, labels: list):
    """Extracts the ordered list of ranked responses from the evaluation text."""
    try:
        # Find the content that comes after "FINAL RANKING:"
        ranking_section = re.search(r"FINAL RANKING:(.*)", text, re.DOTALL | re.IGNORECASE)
        if not ranking_section:
            # Fallback: if the header is missing, try to find any ordered list of labels
            return _extract_labels_in_order(text, labels), text

        ranking_text = ranking_section.group(1).strip()
        # Extract all occurrences of "Response X" in the order they appear
        ranked_labels = _extract_labels_in_order(ranking_text, labels)

        return ranked_labels, text
    except Exception as e:
        print(f"Error parsing ranking text: {e}")
        return [], text

def _extract_labels_in_order(text: str, labels: list):
    """A helper to find all label occurrences in a piece of text and return them in order."""
    # Create a regex pattern to find any of the labels
    # e.g., (Response A|Response B|Response C)
    pattern = "(" + "|".join(re.escape(label) for label in labels) + ")"
    return re.findall(pattern, text)


# --- Stage 3: Synthesize Final Answer ---
async def stage3_synthesize_final(stage1_responses: list, stage2_rankings: list, question: str, api_key: str, chairman_model: str):
    """Async: Asks a chairman model to synthesize the final answer based on all inputs."""
    if not stage1_responses:
        return {"content": "I am sorry, but I was unable to generate a response."}

    # Prepare the context for the chairman model
    s1_text = "\n\n".join([f'{resp["model"]}:\n{resp["content"]}' for resp in stage1_responses])
    s2_text = "\n\n".join([f'Evaluator: {ranking["model"]}\nCritique: {ranking["evaluation_text"]}' for ranking in stage2_rankings])

    synthesis_prompt = (
        f"You are the Chairman of an LLM council. Your task is to synthesize a final, high-quality answer to a user's question based on the submissions and peer reviews from the council members.\n\n"
        f"The user's original question was: \"{question}\".\n\n"
        f"--- STAGE 1: Initial Responses ---\n"
        f"Here are the initial responses from the council members:\n\n{s1_text}\n\n"
        f"--- STAGE 2: Peer Evaluations ---\n"
        f"Here are the peer evaluations of those responses:\n\n{s2_text}\n\n"
        f"--- Your Task ---\n"
        f"Synthesize all of this information into a single, comprehensive, and well-written final answer for the user. "
        f"Your answer should be the definitive response, drawing on the strengths of the best submissions and correcting any identified flaws. "
        f"Do not refer to the stages or the council directly in your final output. Simply provide the best possible answer to the user's question."
    )

    # Query the chairman model
    final_response = await query_models_parallel([chairman_model], synthesis_prompt, api_key)
    return final_response[0] if final_response else {"content": "The chairman failed to generate a response."}

# --- Utility Functions ---
def calculate_aggregate_rankings(stage2_rankings: list, label_to_model: dict):
    """Calculates the aggregate ranking for each model based on peer evaluations."""
    if not stage2_rankings:
        return []

    # Initialize scores for each model
    model_scores = {model: {"total_score": 0, "votes": 0} for model in label_to_model.values()}

    for ranking in stage2_rankings:
        # A ranked list like ["Response C", "Response A", "Response B"]
        ranked_labels = ranking.get("parsed_ranking", [])
        for i, label in enumerate(ranked_labels):
            # Assign points based on rank (e.g., 1st place gets more points)
            score = len(ranked_labels) - i
            model_name = label_to_model.get(label)
            if model_name:
                model_scores[model_name]["total_score"] += score
                model_scores[model_name]["votes"] += 1

    # Calculate average score and sort
    aggregate_rankings = []
    for model, data in model_scores.items():
        if data["votes"] > 0:
            average_score = data["total_score"] / data["votes"]
            aggregate_rankings.append({
                "model": model,
                "average_score": round(average_score, 2),
                "votes": data["votes"]
            })

    # Sort by average score, descending
    return sorted(aggregate_rankings, key=lambda x: x["average_score"], reverse=True)
