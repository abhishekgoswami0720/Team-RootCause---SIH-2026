import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.config.settings import settings

from app.routers import (
    farmer,
    booking,
    queue,
    voice,
    admin
)

from app.middleware.error_handler import (
    global_exception_handler
)


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
    redoc_url="/redoc"
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


# Mount Farmer Feature Phone Simulator
simulator_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "phone-simulator")
if os.path.exists(simulator_dir):
    app.mount("/phone", StaticFiles(directory=simulator_dir, html=True), name="phone-simulator")


@app.get("/simulator", tags=["Simulator"], include_in_schema=False)
def redirect_to_phone():
    return RedirectResponse(url="/phone/")


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
        "status": "healthy"
    }