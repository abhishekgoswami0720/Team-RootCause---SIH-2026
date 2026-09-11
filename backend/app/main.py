from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.database import active_db

from app.routers import (
    farmer,
    booking,
    queue,
    voice,
    admin,
    parv_routes
)

from app.middleware.error_handler import (
    global_exception_handler
)

# Note: tables are created from schema.sql directly (psql -f schema.sql),
# not auto-created on startup. See schema.sql for the source of truth.

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    Backend API for Farmer Procurement Platform.

    This API provides:
    - Farmer management
    - Slot booking
    - Queue management
    - Voice integration
    - Admin operations
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)


app.add_exception_handler(
    Exception,
    global_exception_handler
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    farmer.router,
    prefix="/api/v1"
)

app.include_router(
    booking.router,
    prefix="/api/v1"
)

app.include_router(
    queue.router,
    prefix="/api/v1"
)

app.include_router(
    voice.router,
    prefix="/api/v1"
)

app.include_router(
    admin.router,
    prefix="/api/v1"
)

app.include_router(
    parv_routes.router,
    prefix="/api/v1",
    tags=["Parv - Backend Support"]
)


@app.get("/", tags=["System"])
def root():
    return {
        "message": "Farmer Procurement Platform API",
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "database": active_db()
    }
