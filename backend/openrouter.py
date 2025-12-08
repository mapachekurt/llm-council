"""OpenRouter API client for LLM queries."""

import aiohttp
import asyncio
from typing import Optional, Dict, Any, List


async def query_model(
    session: aiohttp.ClientSession,
    model: str,
    prompt: str,
    api_key: str
) -> Optional[Dict[str, Any]]:
    """Query a single model on OpenRouter and return the response."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/mapachekurt/llm-council",
        "X-Title": "LLM Council"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        async with session.post(
            url,
            headers=headers,
            json=data,
            timeout=aiohttp.ClientTimeout(total=120)
        ) as response:
            if response.status == 200:
                response_data = await response.json()
                content = response_data['choices'][0]['message']['content']
                return {
                    "model": model,
                    "content": content,
                    "reasoning_details": response_data.get('reasoning')
                }
            else:
                error_text = await response.text()
                print(f"Error querying {model}: {response.status} {error_text}")
                return None
    except asyncio.TimeoutError:
        print(f"Timeout while querying {model}")
        return None
    except Exception as e:
        print(f"Exception while querying {model}: {e}")
        return None


async def query_models_parallel(
    models: List[str],
    prompt: str,
    api_key: str
) -> List[Dict[str, Any]]:
    """Query multiple models in parallel and return list of responses."""
    async with aiohttp.ClientSession() as session:
        tasks = [query_model(session, model, prompt, api_key) for model in models]
        results = await asyncio.gather(*tasks)
        # Filter out None results from failed requests
        return [res for res in results if res is not None]
