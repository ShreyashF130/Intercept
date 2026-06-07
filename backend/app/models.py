# backend/app/models.py
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.database import Base

class FuzzSessionRecord(Base):
    __tablename__ = "fuzz_sessions"

    # 1. FIXED: Must be String to accept UUIDs from orchestrator
    id = Column(String, primary_key=True, index=True)
    
    # Multi-Tenant Isolation Key
    organization_id = Column(String, index=True, nullable=False) 
    
    # 2. FIXED: Added tracking metadata used by orchestrator
    schema_name = Column(String, index=True)
    status = Column(String, default="processing")
    result = Column(String, nullable=True)
    
    # Metrics (Aligned naming with orchestrator DB updates)
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    
    # 3. CRITICAL NEW FIX: The JSON payloads for the Dashboard UI
    details = Column(JSON, default=list)
    schema_definition = Column(JSON, default=dict)
    
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