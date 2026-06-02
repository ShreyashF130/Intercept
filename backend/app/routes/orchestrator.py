from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any
import time

# Import SDK engines
from sdk.intercept.fuzzer import generate_fuzz_cases
from sdk.intercept.engine import run_contract_test

# Import Database dependencies
from backend.app.database import get_db
from backend.app.models import FuzzSessionRecord, TestCaseRecord
from sdk.intercept.engine import run_contract_test
from sdk.intercept.multi_provider import generate_content_with_byok
from backend.app.auth import verify_api_key

router = APIRouter(prefix="/api/v1/fuzz", tags=["Orchestrator"])

# Define what the Next.js frontend is allowed to send us
class FuzzTriggerPayload(BaseModel):
    schema_name: str
    schema_definition: Dict[str, Any]
    llm_provider: str
    llm_api_key: str

@router.post("/run", status_code=status.HTTP_201_CREATED)
def trigger_live_fuzz_session(
    payload: FuzzTriggerPayload, 
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Receives a custom schema from the frontend, dynamically generates 
    attacks, runs them, and saves the telemetry to the database.
    """
    print(f"\n🚀 [ORCHESTRATOR] Received live fuzzing request for schema: {payload.schema_name}")
    
    # 1. Ask Gemini to generate the attacks
    attack_prompts = generate_fuzz_cases(
    schema_name=payload.schema_name,
    schema_json_definition=payload.schema_definition,
    llm_provider=payload.llm_provider,
    llm_api_key=payload.llm_api_key,
    count=3
)
    
    if not attack_prompts:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fuzzer failed to generate test cases. Check API keys or Rate Limits."
        )

    # Variables to track the session health
    passed_count = 0
    failed_count = 0
    test_results = []
    
    # Standard instruction for the testing engine
    system_instruction = f"Extract data to create a new {payload.schema_name} object."

    # 2. Fire the attacks at the engine
    for idx, attack_input in enumerate(attack_prompts, 1):
        print(f"💥 Executing Attack Case #{idx}...")
        
        run_report = run_contract_test(
            system_prompt=system_instruction, 
            user_input=attack_input,
            schema_name=payload.schema_name,
            schema_json=payload.schema_definition,
            llm_provider=payload.llm_provider,  # <-- PASS IT HERE
            llm_api_key=payload.llm_api_key
        )
        
        if run_report["status"] == "passed":
            passed_count += 1
        else:
            failed_count += 1
            
        test_results.append({
            "test_id": idx,
            "input_fired": attack_input,
            "engine_status": run_report["status"],
            "model_output": run_report["model_output"],
            "validation_errors": run_report["errors"]
        })
        
        # Jitter to prevent Google API 429 Rate Limits on the free tier
        if idx < len(attack_prompts):
            time.sleep(3)

    # 3. Save everything directly to Supabase
    try:
        db_session_record = FuzzSessionRecord(
            repository="Live-Dashboard-Sandbox",
            total_tests=len(attack_prompts),
            passed_count=passed_count,
            failed_count=failed_count
        )
        db.add(db_session_record)
        db.flush() 

        for test in test_results:
            db_test_case = TestCaseRecord(
                session_id=db_session_record.id,
                test_number=test["test_id"],
                input_fired=test["input_fired"],
                engine_status=test["engine_status"],
                model_output=test["model_output"],
                validation_errors=test["validation_errors"]
            )
            db.add(db_test_case)

        db.commit()
        db.refresh(db_session_record)

        print(f"✅ [ORCHESTRATOR] Success! Session #{db_session_record.id} written to database.")
        
        return {
            "status": "success",
            "message": "Fuzz session complete.",
            "session_id": db_session_record.id,
            "total_tests": len(attack_prompts)
        }

    except Exception as e:
        db.rollback()
        print(f"❌ DB Write Failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to write telemetry to database."
        )