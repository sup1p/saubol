"""
Request and response models for LiveKit API endpoints
"""
from pydantic import BaseModel


class RoomRequest(BaseModel):
    """Request model for room and participant information"""
    room_name: str
    participant_name: str


class TokenResponse(BaseModel):
    """Response model for token generation"""
    token: str
    url: str
    room_name: str


class RoomCreationResponse(BaseModel):
    """Response model for room creation"""
    room_name: str
    sid: str
    message: str


class TranscriptionResponse(BaseModel):
    """Response model for transcription operations"""
    message: str
    room_name: str


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    whisper_model: str


class ApiInfoResponse(BaseModel):
    """Response model for API information"""
    message: str
    endpoints: dict