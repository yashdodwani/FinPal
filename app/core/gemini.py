"""
Gemini 3 API Wrapper
--------------------
Provides run_gemini(payload) → dict
"""

import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in environment.")

# Initialize the new Client (replaces genai.configure)
client = genai.Client(api_key=GEMINI_API_KEY)

# Use the latest Gemini 3 model identifier
MODEL = "gemini-3-pro-preview"

async def run_gemini(payload: dict) -> dict:
    """
    Wrapper around Gemini 3 generate_content.
    Payload format:
    {
      "system_instruction": "...",
      "user": { ... }
    }
    """

    system_instruction = payload.get("system_instruction", "")
    user_obj = payload.get("user")

    # Convert user object to string format
    user_message = f"{user_obj}"

    # Prepare configuration (optional, but good for JSON handling)
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.7
    )

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[user_message],
            config=config
        )

        # New SDK response access
        return response.text.strip()

    except Exception as e:
        # Fallback error handling
        print(f"Gemini API Error: {e}")
        return {"error": "Invalid LLM response format or API error"}