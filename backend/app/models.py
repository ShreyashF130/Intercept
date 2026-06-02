from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.database import Base

class FuzzSessionRecord(Base):
    __tablename__ = "fuzz_sessions"

    id = Column(Integer, primary_key=True, index=True)
    repository = Column(String, index=True)
    total_tests = Column(Integer)
    passed_count = Column(Integer)
    failed_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Establish a one-to-many relationship with the test cases
    tests = relationship("TestCaseRecord", back_populates="session", cascade="all, delete-orphan")

class TestCaseRecord(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("fuzz_sessions.id"))
    test_number = Column(Integer) # e.g., Test 1, Test 2
    
    input_fired = Column(String)
    engine_status = Column(String) # 'passed', 'failed', 'error'
    model_output = Column(JSON, nullable=True)
    validation_errors = Column(JSON, nullable=True)

    # Link back to the parent session
    session = relationship("FuzzSessionRecord", back_populates="tests")