"""
Gemini 3 API Wrapper
--------------------
Provides: run_gemini(payload: dict) → dict
"""

import os
import json
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found in environment.")

# Initialize Client (The 'aio' property will be used for async calls)
client = genai.Client(api_key=GEMINI_API_KEY)

# Gemini 3 Model Identifier
# (Ensure this matches the exact string in Google AI Studio,
# e.g., 'gemini-3-pro-preview' or 'gemini-experimental')
MODEL = "gemini-3-pro-preview"

async def run_gemini(payload: dict) -> dict:
    """
    Wrapper around Gemini 3 generate_content (Async).
    """

    system_instruction = payload.get("system_instruction", "")
    user_obj = payload.get("user", {})

    # Convert user object to string
    user_message = json.dumps(user_obj, indent=2)

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.3,
        # NATIVE JSON MODE: This forces the model to output strict JSON
        response_mime_type="application/json"
    )

    try:
        # CRITICAL CHANGE: Use 'client.aio' and 'await'
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=user_message, # New SDK accepts string directly
            config=config
        )

        # The new SDK creates a .text property on the response
        text_output = response.text

        # Parse the JSON
        # (Since we used response_mime_type, this is very safe)
        return json.loads(text_output)

    except json.JSONDecodeError:
        # Fallback if model returns empty or malformed string
        return {"error": "Malformed JSON", "raw": text_output}

    except Exception as e:
        logging.error(f"Gemini 3 API Error: {e}")
        return {"error": str(e)}