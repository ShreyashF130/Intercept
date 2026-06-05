import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routes import telemetry, dashboard, orchestrator
from backend.app.database import engine, Base

# Build tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Intercept Core Telemetry Gateway",
    version="1.0.0"
)

# Allow Next.js (Port 3000) to talk to FastAPI (Port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://intercept-landing-iota.vercel.app/","http://127.0.0.1:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the routes
app.include_router(telemetry.router)
app.include_router(dashboard.router)
app.include_router(orchestrator.router) # NEW: The Orchestrator Route

@app.get("/healthz", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "intercept-backend"}

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)