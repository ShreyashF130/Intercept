from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.database import get_db
from backend.app.models import FuzzSessionRecord, TestCaseRecord

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])

@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Fetches the latest test sessions to display on the Next.js frontend."""
    try:
        # Fetch the last 10 fuzzing sessions, newest first
        recent_sessions = db.query(FuzzSessionRecord).order_by(desc(FuzzSessionRecord.created_at)).limit(10).all()
        
        # Calculate overall platform health
        total_tests_ever = sum(session.total_tests for session in recent_sessions)
        total_failed_ever = sum(session.failed_count for session in recent_sessions)
        
        failure_rate = 0
        if total_tests_ever > 0:
            failure_rate = round((total_failed_ever / total_tests_ever) * 100, 2)

        # Format the payload for Next.js charts
        session_history = []
        for s in recent_sessions:
            session_history.append({
                "id": s.id,
                "repository": s.repository,
                "date": s.created_at.isoformat() if s.created_at else None,
                "passed": s.passed_count,
                "failed": s.failed_count
            })

        return {
            "status": "success",
            "global_failure_rate": failure_rate,
            "total_tests_tracked": total_tests_ever,
            "recent_sessions": session_history
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}