# action/main.py
import os
import sys
import json
import time
import requests
from extractor import extract_schema_from_py_file

def main():
    print("🛡️ Starting Intercept CI/CD Security Gate...")

    schema_file = os.getenv("SCHEMA_FILE")
    schema_name = os.getenv("SCHEMA_NAME")
    api_key = os.getenv("API_KEY")
    backend_url = os.getenv("BACKEND_URL")
    llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    llm_api_key = os.getenv("LLM_API_KEY")

    if not all([schema_file, schema_name, api_key, backend_url, llm_api_key]):
        print("❌ ERROR: Missing required GitHub Action configuration parameters.")
        sys.exit(1)

    # AST Dynamic extraction 
    if schema_file.endswith(".py"):
        schema_definition = extract_schema_from_py_file(schema_file, schema_name)
        if not schema_definition:
            sys.exit(1)
    else:
        try:
            with open(schema_file, 'r') as f:
                schema_definition = json.load(f)
        except Exception as e:
            print(f"❌ ERROR: Failed to load static JSON: {str(e)}")
            sys.exit(1)

    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    payload = {
        "schema_name": schema_name,
        "schema_definition": schema_definition,
        "llm_provider": llm_provider,
        "llm_api_key": llm_api_key
    }

    try:
        # 1. Dispatch background request to api gateway
        response = requests.post(backend_url, json=payload, headers=headers)
        response.raise_for_status()
        dispatch_data = response.json()
        
        session_id = dispatch_data.get("session_id")
        print(f"✅ Pipeline dispatched successfully. Session Tracking ID: {session_id}")
        print("⏳ Processing adversarial security attacks in background, monitoring status...")

        # Derive status checking endpoint from base endpoint path parsing
        base_url = backend_url.split("/api/v1/fuzz/run")[0]
        status_endpoint = f"{base_url}/api/v1/fuzz/status/{session_id}"

        # 2. Enter industrial polling loop
        timeout_limit = 120  # Max 2 minutes fallback protection
        start_time = time.time()

        while time.time() - start_time < timeout_limit:
            time.sleep(4)  # Wait 4 seconds between poll sweeps
            
            status_response = requests.get(status_endpoint, headers={"X-API-Key": api_key})
            status_response.raise_for_status()
            current_state = status_response.json()

            state_status = current_state.get("status")

            if state_status == "processing":
                print("🔄 Fuzzer actively attacking contract types... checking again...")
                continue
                
            elif state_status == "completed":
                print("\n📊 --- INTERCEPT SECURITY AUDIT REPORT ---")
                print(f"Result Flag:  [{current_state.get('result').upper()}]")
                print(f"Total Attacks: {current_state.get('total_tests')}")
                print(f"Passed:        {current_state.get('passed_tests')}")
                print(f"Failed:        {current_state.get('failed_tests')}")
                print("------------------------------------------\n")

                if current_state.get("result") == "failed":
                    print("❌ SECURITY ERROR: AI generation broke type contracts. PR Blocked.")
                    sys.exit(1)
                
                print("🛡️ Validation verified clean. All hallucinations mitigated successfully.")
                sys.exit(0)

            elif state_status == "failed" or "error" in current_state:
                print(f"❌ PIPELINE FAILURE: {current_state.get('error', 'Execution Error occurred.')}")
                sys.exit(1)

        print("❌ TIMEOUT: The security engine gate exceeded response runtime allocations.")
        sys.exit(1)

    except Exception as e:
        print(f"❌ CRITICAL CONNECTIVITY EXCEPTION: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()