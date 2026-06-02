import os
import sys
import json
import requests
from extractor import extract_schema_from_py_file

def main():
    print("🛡️ Starting Intercept CI/CD Security Gate...")

    schema_file = os.getenv("SCHEMA_FILE")
    schema_name = os.getenv("SCHEMA_NAME")
    api_key = os.getenv("API_KEY")
    backend_url = os.getenv("BACKEND_URL")
    # New BYOK variables
    llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    llm_api_key = os.getenv("LLM_API_KEY")

    if not all([schema_file, schema_name, api_key, backend_url, llm_api_key]):
        print("❌ ERROR: Missing required GitHub Action inputs or Provider Keys.")
        sys.exit(1)

    # Automatically handle raw python files via AST or static JSON files
    if schema_file.endswith(".py"):
        print(f"📂 Extracting Pydantic class '{schema_name}' dynamically...")
        schema_definition = extract_schema_from_py_file(schema_file, schema_name)
        if not schema_definition:
            sys.exit(1)
    else:
        print(f"📂 Parsing static JSON schema file...")
        try:
            with open(schema_file, 'r') as f:
                schema_definition = json.load(f)
        except Exception as e:
            print(f"❌ ERROR: Failed to load JSON schema file: {str(e)}")
            sys.exit(1)

    print(f"🚀 Dispatching contract pipeline via Provider: [{llm_provider}]...")
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    # Send both the schema and the user's keys safely over HTTPS
    payload = {
        "schema_name": schema_name,
        "schema_definition": schema_definition,
        "llm_provider": llm_provider,
        "llm_api_key": llm_api_key
    }

    try:
        response = requests.post(backend_url, json=payload, headers=headers)
        if response.status_code in [401, 403]:
            print("❌ SECURITY ERROR: Invalid Intercept Platform Key.")
            sys.exit(1)
        response.raise_for_status()
        result_data = response.json()
        
        print(f"✅ Intercept fuzzing complete. Session ID: {result_data.get('session_id')}")
        sys.exit(0)
    except Exception as e:
        print(f"❌ PIPELINE ERROR: Failed to execute contract test: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()