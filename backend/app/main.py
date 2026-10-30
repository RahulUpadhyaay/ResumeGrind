import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import router as api_router

# WHY: We modularize the FastAPI application structure to keep main.py clean and routes separated.

app = FastAPI(
    title="ResumeGrind API",
    description="Backend API for AI Voice Mock Interviewer",
    version="1.0.0"
)

# WHY: Middleware to calculate exact server processing latency (X-Process-Time-Ms).
# This provides empirical latency metrics for candidate performance reports & resume points.
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time_ms = int((time.time() - start_time) * 1000)
    response.headers["X-Process-Time-Ms"] = str(process_time_ms)
    print(f"[LATENCY] [{request.method}] {request.url.path} -> {response.status_code} ({process_time_ms}ms)")
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {
        "message": "Welcome to ResumeGrind API",
        "environment": settings.ENVIRONMENT
    }
