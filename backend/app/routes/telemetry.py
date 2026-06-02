from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Any

# Import your DB dependency and SQLAlchemy models
from backend.app.database import get_db
from backend.app.models import FuzzSessionRecord, TestCaseRecord

from backend.app.auth import verify_api_key

router = APIRouter(prefix="/api/v1/telemetry", tags=["Telemetry"])

class TestCaseResult(BaseModel):
    test_id: int
    input_fired: str
    engine_status: str
    model_output: Optional[Any] = None
    validation_errors: Optional[Any] = None

class FuzzSessionPayload(BaseModel):
    repository: str
    total_tests: int
    passed_count: int
    failed_count: int
    results: List[TestCaseResult]

@router.post("/submit", status_code=status.HTTP_201_CREATED)
async def receive_fuzz_telemetry(
    payload: FuzzSessionPayload, 
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Ingests testing reports and permanently stores them in PostgreSQL/Supabase.
    """
    try:
        # 1. Create the parent Session Record
        db_session_record = FuzzSessionRecord(
            repository=payload.repository,
            total_tests=payload.total_tests,
            passed_count=payload.passed_count,
            failed_count=payload.failed_count
        )
        db.add(db_session_record)
        db.flush() # Flushes to get the auto-generated ID without committing yet

        # 2. Create the child Test Case Records
        for test in payload.results:
            db_test_case = TestCaseRecord(
                session_id=db_session_record.id,
                test_number=test.test_id,
                input_fired=test.input_fired,
                engine_status=test.engine_status,
                model_output=test.model_output,
                validation_errors=test.validation_errors
            )
            db.add(db_test_case)

        # 3. Commit the entire transaction
        db.commit()
        db.refresh(db_session_record)

        print(f"✅ DB Write Success: Session #{db_session_record.id} written to Supabase.")
        
        return {
            "status": "success",
            "message": "Telemetry permanently saved to database.",
            "session_id": db_session_record.id
        }

    except Exception as e:
        db.rollback()
        print(f"❌ DB Write Failed: {str(e)}")
        return {"status": "error", "message": "Failed to write to database."}