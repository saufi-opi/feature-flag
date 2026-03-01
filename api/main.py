from fastapi import FastAPI
from contextlib import asynccontextmanager
from infrastructure.database import init_db
from api.routes import router as flags_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist before handling requests
    init_db()
    yield

app = FastAPI(
    title="Feature Flag Engine API",
    description="A robust, framework-agnostic feature flag system built in pure Python.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(flags_router)

@app.get("/", tags=["system"])
def root():
    """Root endpoint to ensure the API is running."""
    return {"message": "Feature Flag Engine API is running."}

@app.get("/health", tags=["system"])
def health_check():
    """Health check endpoint to ensure the API is running."""
    return {"status": "ok"}
