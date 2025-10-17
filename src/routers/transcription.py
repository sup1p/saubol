"""
Transcription management API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from src.schemas.livekit import TranscriptionResponse
from src.services.transcription import TranscriptionSession
from src.core.dependencies import get_active_sessions

router = APIRouter(prefix="/api", tags=["transcription"])


@router.post("/start-transcription", response_model=TranscriptionResponse)
async def start_transcription(
    room_name: str,
    sessions: dict = Depends(get_active_sessions)
):
    """
    Start transcription service for a room.
    
    Args:
        room_name: Name of the room to transcribe
        sessions: Active sessions dependency injection
        
    Returns:
        Confirmation of transcription start
    """
    try:
        # Check if transcription already running for this room
        if room_name in sessions:
            raise HTTPException(
                status_code=400,
                detail=f"Transcription already running for room: {room_name}"
            )
        
        # Create and connect transcription session
        session = TranscriptionSession(room_name)
        await session.connect()
        
        # Store session
        sessions[room_name] = session
        
        return TranscriptionResponse(
            message="Transcription started",
            room_name=room_name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error starting transcription: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start transcription: {str(e)}")


@router.post("/stop-transcription", response_model=TranscriptionResponse)
async def stop_transcription(
    room_name: str,
    sessions: dict = Depends(get_active_sessions)
):
    """
    Stop transcription service for a room.
    
    Args:
        room_name: Name of the room to stop transcribing
        sessions: Active sessions dependency injection
        
    Returns:
        Confirmation of transcription stop
    """
    try:
        # Check if transcription exists
        if room_name not in sessions:
            raise HTTPException(
                status_code=404,
                detail=f"No active transcription found for room: {room_name}"
            )
        
        # Get and disconnect session
        session = sessions[room_name]
        await session.disconnect()
        
        # Remove from active sessions
        del sessions[room_name]
        
        return TranscriptionResponse(
            message="Transcription stopped",
            room_name=room_name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error stopping transcription: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop transcription: {str(e)}")