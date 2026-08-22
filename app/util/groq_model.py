import os
import httpx

# Ordered priority list — best model first, fallback down the list
PREFERRED_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "llama3-8b-8192",
]

def get_best_groq_model() -> str:
    """
    Queries the Groq API for currently available models and returns
    the best one from our priority list. Falls back gracefully if the
    API call fails.
    """
    api_key = os.environ.get("GROQ_API_KEY", "")
    
    try:
        response = httpx.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=5.0,
        )
        response.raise_for_status()
        available_ids = {m["id"] for m in response.json().get("data", [])}

        for model in PREFERRED_MODELS:
            if model in available_ids:
                print(f"[InsightAI] Using Groq model: {model}")
                return model

    except Exception as e:
        print(f"[InsightAI] Could not fetch Groq models, using default. Reason: {e}")

    # Hard fallback — return first in priority list
    return PREFERRED_MODELS[0]
