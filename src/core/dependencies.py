"""
FastAPI dependencies for dependency injection
"""
from typing import Dict
from .settings import settings
from ..services.transcription import TranscriptionSession


# Store active transcription sessions
active_sessions: Dict[str, TranscriptionSession] = {}


def get_settings():
    """Get application settings"""
    return settings


def get_active_sessions() -> Dict[str, TranscriptionSession]:
    """Get active transcription sessions"""
    return active_sessions