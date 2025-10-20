"""
Real-time Speech-to-Text API using FastAPI, LiveKit, and Whisper

This is the main application entry point that initializes the FastAPI application
and includes all the routers for different endpoints.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.settings import settings
from src.routers import rooms
from src.schemas.livekit import ApiInfoResponse, HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    yield
    
    # Shutdown - cleanup all active transcription agents
    print("Shutting down, cleaning up transcription agents...")
    from src.agents.transcription import TranscriptionAgentManager
    
    # Stop all active agents
    active_rooms = TranscriptionAgentManager.get_active_rooms()
    for room_name in active_rooms:
        await TranscriptionAgentManager.stop_agent_for_room(room_name)
        print(f"Stopped agent for room: {room_name}")


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="Real-time Speech-to-Text API using FastAPI, LiveKit, and Whisper",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rooms.router)


@app.get("/", response_model=ApiInfoResponse)
async def root():
    """Root endpoint with API information"""
    return ApiInfoResponse(
        message="Speech-to-Text API with LiveKit",
        endpoints={
            "create_room": "/api/create-room",
            "generate_token": "/api/token",
            "start_transcription": "/api/start-transcription",
            "stop_transcription": "/api/stop-transcription",
            "start_agent": "/api/start-agent",
            "health": "/health"
        }
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy"
    )
