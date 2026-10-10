import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("LLM_API_KEY", "")
model_name = os.getenv("LLM_MODEL", "gemini-2.5-flash")

print(f"Testing Gemini with custom httpx client (verify=False)...")
print(f"API Key present: {bool(api_key)}")

try:
    from google import genai
    from google.genai import types
    
    # Custom httpx client bypassing local SSL handshake blocks
    custom_httpx = httpx.Client(verify=False, timeout=30.0)
    http_opts = types.HttpOptions(httpxClient=custom_httpx)
    
    client = genai.Client(api_key=api_key, http_options=http_opts)
    
    response = client.models.generate_content(
        model=model_name,
        contents="Say 'Gemini is connected and working perfectly!'",
    )
    print("\nSUCCESS! Gemini Response:")
    print(response.text)
except Exception as e:
    print(f"\nFailed with custom client: {e}")
    # Try gemini-1.5-flash as fallback model
    try:
        custom_httpx = httpx.Client(verify=False, timeout=30.0)
        http_opts = types.HttpOptions(httpxClient=custom_httpx)
        client = genai.Client(api_key=api_key, http_options=http_opts)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents="Say 'Gemini is connected and working perfectly!'",
        )
        print("\nSUCCESS with gemini-1.5-flash! Gemini Response:")
        print(response.text)
    except Exception as e2:
        print(f"\nFallback gemini-1.5-flash failed: {e2}")
