import json
from google import genai
from google.genai import types
from openai import OpenAI
from anthropic import Anthropic

def generate_content_with_byok(provider: str, api_key: str, system_instruction: str, user_prompt: str, json_schema: dict = None) -> str:
    """
    A unified execution layer that accepts any vendor API key, routes 
    the traffic to that provider, and enforces strict raw JSON output strings.
    """
    provider = provider.strip().lower()

    # 1. GOOGLE GEMINI ROUTE
    if provider == "gemini":
        try:
            client = genai.Client(api_key=api_key)
            # Use structure constraints if supported, else fallback to standard generation
            config_args = {"temperature": 0.7}
            if json_schema:
                config_args["response_mime_type"] = "application/json"
                
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(**config_args)
            )
            return response.text
        except Exception as e:
            print(f"[BYOK-Gemini] Execution Error: {str(e)}")
            return "{}"

    # 2. OPENAI ROUTE
    elif provider == "openai":
        try:
            client = OpenAI(api_key=api_key)
            kwargs = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7
            }
            if json_schema:
                kwargs["response_format"] = {"type": "json_object"}
                
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            print(f"[BYOK-OpenAI] Execution Error: {str(e)}")
            return "{}"

    # 3. ANTHROPIC CLAUDE ROUTE
    elif provider == "anthropic":
        try:
            client = Anthropic(api_key=api_key)
            # Claude expects system prompts separately
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1000,
                temperature=0.7,
                system=system_instruction + " You must output valid JSON only.",
                messages=[{"role": "user", "content": user_prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"[BYOK-Anthropic] Execution Error: {str(e)}")
            return "{}"

    else:
        print(f"❌ Unsupported provider passed: {provider}")
        return "{}"