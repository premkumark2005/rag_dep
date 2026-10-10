import os
import sys
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("LLM_API_KEY", "")
model_name = os.getenv("LLM_MODEL", "gemini-2.5-flash")

print(f"Testing Gemini API call...")
print(f"Model: {model_name}")
print(f"API Key present: {bool(api_key)}")

if not api_key:
    print("ERROR: LLM_API_KEY is empty in .env!")
    sys.exit(1)

try:
    from google import genai
    from google.genai import types
    
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=30))
    
    # Try gemini-2.5-flash first, or gemini-2.0-flash / gemini-1.5-flash
    response = client.models.generate_content(
        model=model_name,
        contents="Say 'Gemini is working successfully!'",
    )
    print("\nSUCCESS! Gemini Response:")
    print(response.text)
except Exception as e:
    print(f"\nFailed with model '{model_name}': {e}")
    # Let's try fallback model names if gemini-2.5-flash has an issue
    fallback_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-pro"]
    for fb in fallback_models:
        if fb == model_name:
            continue
        print(f"\nTrying fallback model '{fb}'...")
        try:
            client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=30))
            response = client.models.generate_content(
                model=fb,
                contents="Say 'Gemini is working successfully!'",
            )
            print(f"SUCCESS with model '{fb}'! Gemini Response:")
            print(response.text)
            print(f"\n--> SUGGESTION: Update LLM_MODEL={fb} in .env!")
            break
        except Exception as fb_err:
            print(f"Fallback model '{fb}' failed: {fb_err}")
