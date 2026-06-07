import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.database import get_db
from backend.app.models import FuzzSessionRecord

# ---> THE ROUTER FIX <---
router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])

@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Fetches the latest test sessions to display on the Next.js frontend."""
    try:
        recent_sessions = db.query(FuzzSessionRecord).order_by(desc(FuzzSessionRecord.created_at)).limit(10).all()
        
        total_tests_ever = 0
        total_failed_ever = 0

        session_history = []
        for s in recent_sessions:
            t_tests = getattr(s, 'total_tests', getattr(s, 'total_count', 0)) or 0
            f_tests = getattr(s, 'failed_tests', getattr(s, 'failed_count', 0)) or 0
            p_tests = getattr(s, 'passed_tests', getattr(s, 'passed_count', 0)) or 0
            
            total_tests_ever += t_tests
            total_failed_ever += f_tests
            
            session_history.append({
                "id": str(s.id),
                "schema_name": getattr(s, 'schema_name', 'Dynamic Schema'),
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "passed_tests": p_tests,
                "failed_tests": f_tests,
                "status": getattr(s, 'status', 'completed'),
                "result": getattr(s, 'result', 'failed'),
                "details": s.details if isinstance(getattr(s, 'details', []), list) else json.loads(getattr(s, 'details', '[]') or '[]'),
                "schema_definition": s.schema_definition if isinstance(getattr(s, 'schema_definition', {}), dict) else json.loads(getattr(s, 'schema_definition', '{}') or '{}'),
                "ai_analysis": getattr(s, 'ai_analysis', 'Analysis pending...')
            })

        failure_rate = 0
        if total_tests_ever > 0:
            failure_rate = round((total_failed_ever / total_tests_ever) * 100, 2)

        return {
            "status": "success",
            "global_failure_rate": failure_rate,
            "total_tests_tracked": total_tests_ever,
            "recent_sessions": session_history
        }

    except Exception as e:
        print(f"❌ DASHBOARD ERROR: {str(e)}")
        return {"status": "error", "message": str(e)}