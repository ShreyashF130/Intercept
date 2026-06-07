# backend/app/routes/orchestrator.py
import json
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any
from sqlalchemy import text 

from sdk.intercept.fuzzer import generate_fuzz_cases
from sdk.intercept.engine import run_contract_test
from backend.app.auth import authenticate_tenant
from backend.app.database import SessionLocal

router = APIRouter()
SESSION_CACHE: Dict[str, Dict[str, Any]] = {}

class FuzzTriggerPayload(BaseModel):
    schema_name: str
    schema_definition: Dict[str, Any]
    llm_provider: str
    llm_api_key: str

def async_fuzz_processor(session_id: str, payload: FuzzTriggerPayload, organization_id: str):
    db = SessionLocal()
    try:
        attack_prompts = generate_fuzz_cases(
            schema_name=payload.schema_name,
            schema_json_definition=payload.schema_definition,
            llm_provider=payload.llm_provider,
            llm_api_key=payload.llm_api_key,
            count=3
        )
        
        if not attack_prompts:
            db.execute(
                text("UPDATE fuzz_sessions SET status = 'failed' WHERE id = :id"),
                {"id": session_id}
            )
            db.commit()
            SESSION_CACHE[session_id] = {"status": "failed", "error": "Fuzz generation failed."}
            return

        reports = []
        passed_count = 0

        for attack_input in attack_prompts:
            run_report = run_contract_test(
                system_prompt="You are a strict database ingestion contract validator.",
                user_input=attack_input,
                schema_name=payload.schema_name,
                schema_json=payload.schema_definition,
                llm_provider=payload.llm_provider,
                llm_api_key=payload.llm_api_key
            )
            
            # Map user_input directly into the report so the frontend can read it
            run_report["user_input"] = attack_input 
            reports.append(run_report)
            
            test_status = run_report.get("status", "failed")
            if test_status == "passed":
                passed_count += 1

            db.execute(
                text("""
                INSERT INTO test_cases (session_id, input_payload, error_message, status)
                VALUES (:session_id, :input_payload, :error_message, :status)
                """),
                {
                    "session_id": session_id,
                   "input_payload": json.dumps(attack_input),
                    "error_message": run_report.get("error"),
                    "status": test_status
                }
            )

        final_result = "passed" if passed_count == len(attack_prompts) else "failed"

        # CRITICAL FIX: Save the details array to the database
        db.execute(
            text("""
            UPDATE fuzz_sessions 
            SET status = 'completed', result = :result, total_tests = :total, 
                passed_tests = :passed, failed_tests = :failed, details = :details
            WHERE id = :id
            """),
            {
                "id": session_id,
                "result": final_result,
                "total": len(attack_prompts),
                "passed": passed_count,
                "failed": len(attack_prompts) - passed_count,
                "details": json.dumps(reports) 
            }
        )
        db.commit()

        SESSION_CACHE[session_id] = {
            "status": "completed",
            "result": final_result,
            "total_tests": len(attack_prompts),
            "passed_tests": passed_count,
            "failed_tests": len(attack_prompts) - passed_count,
            "details": reports,
            "organization_id": organization_id
        }

    except Exception as e:
        print(f"❌ DATABASE WORKER ERROR: {str(e)}") 
        db.rollback()
        db.execute(text("UPDATE fuzz_sessions SET status = 'failed' WHERE id = :id"), {"id": session_id})
        db.commit()
        SESSION_CACHE[session_id] = {"status": "failed", "error": str(e)}
    finally:
        db.close()

@router.post("/api/v1/fuzz/run", status_code=status.HTTP_202_ACCEPTED)
def trigger_fuzz_pipeline(
    payload: FuzzTriggerPayload, 
    background_tasks: BackgroundTasks,
    tenant_context: dict = Depends(authenticate_tenant)
):
    session_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        # CRITICAL FIX: Save the schema_definition on initial insert
        db.execute(
            text("""
            INSERT INTO fuzz_sessions (id, organization_id, schema_name, status, schema_definition)
            VALUES (:id, :org_id, :schema, 'processing', :schema_def)
            """),
            {
                "id": session_id, 
                "org_id": tenant_context["organization_id"], 
                "schema": payload.schema_name,
                "schema_def": json.dumps(payload.schema_definition)
            }
        )
        db.commit()
    except Exception as e:
        print(f"❌ DATABASE INSERT ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initialize session in database.")
    finally:
        db.close()

    SESSION_CACHE[session_id] = {
        "status": "processing",
        "organization_id": tenant_context["organization_id"]
    }
    
    background_tasks.add_task(async_fuzz_processor, session_id, payload, tenant_context["organization_id"])
    
    return {
        "status": "accepted",
        "session_id": session_id,
        "message": "Fuzz testing pipeline successfully initiated in background."
    }