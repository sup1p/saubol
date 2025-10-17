"""
Transcription management API endpoints
"""
from fastapi import APIRouter, HTTPException
from src.schemas.livekit import TranscriptionResponse
from src.services.transcription import TranscriptionAgentManager
import logging

router = APIRouter(prefix="/api", tags=["transcription"])
logger = logging.getLogger(__name__)


@router.post("/start-transcription", response_model=TranscriptionResponse)
async def start_transcription(room_name: str):
    """
    Start transcription agent for a specific room.
    
    Args:
        room_name: Name of the LiveKit room to start transcription for
        
    Returns:
        Confirmation of transcription start
    """
    try:
        # Check if agent already running for this room
        active_rooms = TranscriptionAgentManager.get_active_rooms()
        if room_name in active_rooms:
            raise HTTPException(
                status_code=400,
                detail=f"Transcription agent already running for room: {room_name}"
            )
        
        # Start transcription agent for this room
        success = await TranscriptionAgentManager.start_agent_for_room(room_name)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start transcription agent for room: {room_name}"
            )
        
        logger.info(f"Started transcription agent for room: {room_name}")
        return TranscriptionResponse(
            message="Transcription agent started successfully",
            room_name=room_name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting transcription for room {room_name}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to start transcription: {str(e)}"
        )


@router.post("/stop-transcription", response_model=TranscriptionResponse)
async def stop_transcription(room_name: str):
    """
    Stop transcription agent for a specific room.
    
    Args:
        room_name: Name of the LiveKit room to stop transcription for
        
    Returns:
        Confirmation of transcription stop
    """
    try:
        # Check if agent exists for this room
        active_rooms = TranscriptionAgentManager.get_active_rooms()
        if room_name not in active_rooms:
            raise HTTPException(
                status_code=404,
                detail=f"No active transcription agent found for room: {room_name}"
            )
        
        # Stop transcription agent for this room
        success = await TranscriptionAgentManager.stop_agent_for_room(room_name)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to stop transcription agent for room: {room_name}"
            )
        
        logger.info(f"Stopped transcription agent for room: {room_name}")
        return TranscriptionResponse(
            message="Transcription agent stopped successfully",
            room_name=room_name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping transcription for room {room_name}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to stop transcription: {str(e)}"
        )


@router.get("/active-transcriptions")
async def get_active_transcriptions():
    """
    Get list of rooms with active transcription agents.
    
    Returns:
        List of active room names
    """
    try:
        active_rooms = TranscriptionAgentManager.get_active_rooms()
        return {
            "message": f"Found {len(active_rooms)} active transcription agents",
            "active_rooms": active_rooms
        }
    except Exception as e:
        logger.error(f"Error getting active transcriptions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get active transcriptions: {str(e)}"
        )