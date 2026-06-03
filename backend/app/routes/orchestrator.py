# backend/app/routes/orchestrator.py
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid

from sdk.intercept.fuzzer import generate_fuzz_cases
from sdk.intercept.engine import run_contract_test

router = APIRouter()

# In-memory storage cache for execution statuses.
# NOTE: For production, you will save/update these states in your Supabase DB.
SESSION_CACHE: Dict[str, Dict[str, Any]] = {}

class FuzzTriggerPayload(BaseModel):
    schema_name: str
    schema_definition: Dict[str, Any]
    llm_provider: str
    llm_api_key: str

def async_fuzz_processor(session_id: str, payload: FuzzTriggerPayload):
    """
    Asynchronous worker task that handles the heavy LLM fuzzing loop 
    outside the main request/response thread.
    """
    try:
        # 1. Generate adversarial attack prompts
        attack_prompts = generate_fuzz_cases(
            schema_name=payload.schema_name,
            schema_json_definition=payload.schema_definition,
            llm_provider=payload.llm_provider,
            llm_api_key=payload.llm_api_key,
            count=3
        )
        
        if not attack_prompts:
            SESSION_CACHE[session_id] = {
                "status": "failed",
                "error": f"Fuzz generation failed. Verify that your [{payload.llm_provider}] API key is valid."
            }
            return

        reports = []
        passed_count = 0

        # 2. Execute contract structural verification
        for attack_input in attack_prompts:
            run_report = run_contract_test(
                system_prompt="You are a strict database ingestion contract validator.",
                user_input=attack_input,
                schema_name=payload.schema_name,
                schema_json=payload.schema_definition,
                llm_provider=payload.llm_provider,
                llm_api_key=payload.llm_api_key
            )
            reports.append(run_report)
            if run_report.get("status") == "passed":
                passed_count += 1

        # Determine pipeline threshold success status
        final_status = "passed" if passed_count == len(attack_prompts) else "failed"

        # 3. Save finalized telemetry data back to cache/DB
        SESSION_CACHE[session_id] = {
            "status": "completed",
            "result": final_status,
            "total_tests": len(attack_prompts),
            "passed_tests": passed_count,
            "failed_tests": len(attack_prompts) - passed_count,
            "details": reports
        }

    except Exception as e:
        SESSION_CACHE[session_id] = {
            "status": "failed",
            "error": f"Internal Worker Error: {str(e)}"
        }

@router.post("/api/v1/fuzz/run", status_code=status.HTTP_202_ACCEPTED)
def trigger_fuzz_pipeline(payload: FuzzTriggerPayload, background_tasks: BackgroundTasks):
    """
    Receives payload, spawns worker, instantly drops response back to runner.
    """
    print(f"🚀 [ASYNC GATEWAY] Dispatched tracking run for schema: {payload.schema_name}")
    
    # Generate unique session tracker id
    session_id = str(uuid.uuid4())
    
    # Register pending state initialization
    SESSION_CACHE[session_id] = {"status": "processing"}
    
    # Hand execution logic entirely off to thread pool worker
    background_tasks.add_task(async_fuzz_processor, session_id, payload)
    
    # Return 202 instantly
    return {
        "status": "accepted",
        "session_id": session_id,
        "message": "Fuzz testing pipeline successfully initiated in background."
    }

@router.get("/api/v1/fuzz/status/{session_id}")
def check_pipeline_status(session_id: str):
    """
    Tracking endpoint hit repeatedly by GitHub Action script to poll progress metrics.
    """
    if session_id not in SESSION_CACHE:
        raise HTTPException(status_code=404, detail="Requested fuzzing session not found.")
    
    return SESSION_CACHE[session_id]