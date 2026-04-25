import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, create_engine, Session
from contextlib import asynccontextmanager

# Configuration from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://music:changeme123@postgres:5432/music_streaming")
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print(f"Starting up application...")
    yield
    # Shutdown
    print(f"Shutting down application...")


app = FastAPI(
    title="Music Streaming API",
    description="Music streaming service backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database setup (sync for now, will be async later)
def get_database_url() -> str:
    """Get database URL, converting postgresql+asyncpg to postgresql for sync engine."""
    url = DATABASE_URL
    if url.startswith("postgresql+asyncpg"):
        url = url.replace("postgresql+asyncpg", "postgresql+psycopg")
    return url


engine = None


def get_engine():
    """Get or create database engine."""
    global engine
    if engine is None:
        db_url = get_database_url()
        engine = create_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
        )
    return engine


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    try:
        eng = get_engine()
        SQLModel.metadata.create_all(eng)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Warning: Could not create database tables: {e}")


@app.get("/health")
async def healthcheck():
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "service": "music-streaming-backend",
        "version": "1.0.0",
    }
    
    # Check database connection
    try:
        eng = get_engine()
        with Session(eng) as session:
            session.exec("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"disconnected: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Music Streaming API",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVER_HOST, port=8000)
