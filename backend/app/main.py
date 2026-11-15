import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import init_db
from app.api.v1.router import api_v1_router
from app.api.v1.health import get_health_status
from app.database import get_db
from fastapi import Depends
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("forensight")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to initialize resources safely."""
    logger.info("Initializing ForenSight Forensic Storage & SQLite Schema...")
    init_db()
    logger.info("Database and storage directories successfully initialized.")
    yield
    logger.info("ForenSight backend shutdown complete.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="ForenSight - Digital Forensics Investigation Toolkit API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Development-only CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Direct /api/health endpoint as required by Phase 1 Task 7
@app.get("/api/health", tags=["Health & Diagnostics"])
def direct_health_check(db: Session = Depends(get_db)):
    """Direct root /api/health endpoint."""
    return get_health_status(db=db)


# Versioned API routes under /api/v1
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "ONLINE",
        "docs": "/docs",
        "health": "/api/health",
    }
