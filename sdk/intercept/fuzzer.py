# sdk/intercept/fuzzer.py
import json
import time
from sdk.intercept.multi_provider import generate_content_with_byok

def generate_fuzz_cases(
    schema_name: str, 
    schema_json_definition: dict, 
    llm_provider: str,    # <-- NEW: Pass the user's provider
    llm_api_key: str,     # <-- NEW: Pass the user's key
    count: int = 3
) -> list:
    """
    Generates adversarial inputs dynamically using the user's own provider and API key.
    Includes robust retry logic for API limits.
    """
    formatted_schema = json.dumps(schema_json_definition, indent=2)
    
    system_instruction = "You are an expert QA Automation Engineer specializing in fuzz testing AI agents."
    
    fuzzer_prompt = f"""
    Generate exactly {count} distinct user text inputs designed to trick an AI agent into breaking the following JSON Schema structure named '{schema_name}':
    {formatted_schema}
    
    Focus on breaking data types, violating required fields, and injecting unsupported options.
    Output a raw JSON list of strings representing user prompts. Example format:
    ["prompt 1", "prompt 2", "prompt 3"]
    
    CRITICAL: Output valid, clean JSON only. Do not include markdown wraps or backticks.
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Route generation costs entirely to the user's credentials
            raw_response = generate_content_with_byok(
                provider=llm_provider,
                api_key=llm_api_key,
                system_instruction=system_instruction,
                user_prompt=fuzzer_prompt,
                json_schema=None  # Keep raw text retrieval for the prompt list arrays
            )
            
            cleaned_output = raw_response.strip()
            if cleaned_output.startswith("```json"):
                cleaned_output = cleaned_output[7:]
            if cleaned_output.endswith("```"):
                cleaned_output = cleaned_output[:-3]
            cleaned_output = cleaned_output.strip()
            
            return json.loads(cleaned_output)
        
        except Exception as e:
            error_msg = str(e)
            # Catch rate limit indicators across OpenAI, Gemini, and Anthropic
            if any(indicator in error_msg.upper() for indicator in ["429", "RESOURCE_EXHAUSTED", "RATE_LIMIT"]):
                wait_time = 30 * (attempt + 1)
                print(f"⚠️ [Fuzzer] Rate Limit Hit for {llm_provider}. Auto-waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"❌ Failed to generate fuzz cases: {error_msg}")
                return []
                
    print("❌ Exhausted all API retries. Aborting fuzzer.")
    return []