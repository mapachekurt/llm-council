import aiohttp
import asyncio
import os
import json

# The API key is now passed as an argument to the functions
# that need it, making the functions more pure and testable.

async def query_model(session, model: str, prompt: str, api_key: str):
    """Queries a single model on OpenRouter and returns the response."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                response_data = await response.json()
                content = response_data['choices'][0]['message']['content']
                # The structure might include reasoning details, so we return a dictionary.
                return {
                    "model": model,
                    "content": content,
                    "reasoning_details": response_data.get('reasoning') # Example of extracting more data
                }
            else:
                print(f"Error querying {model}: {response.status} {await response.text()}")
                return None
    except Exception as e:
        print(f"Exception while querying {model}: {e}")
        return None

async def query_models_parallel(models: list, prompt: str, api_key: str):
    """Queries multiple models in parallel and returns a list of their responses."""
    async with aiohttp.ClientSession() as session:
        tasks = [query_model(session, model, prompt, api_key) for model in models]
        results = await asyncio.gather(*tasks)
        # Filter out None results from failed requests
        return [res for res in results if res is not None]
