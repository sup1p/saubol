"""
Room management API endpoints
"""
from fastapi import APIRouter, HTTPException
from src.schemas.livekit import RoomCreationResponse, TokenResponse, RoomRequest
from src.utils.auth import create_room, generate_access_token
from src.utils.room import list_rooms
from src.core.settings import settings

router = APIRouter(prefix="/api", tags=["rooms"])


@router.post("/token", response_model=TokenResponse)
async def generate_token(request: RoomRequest):
    """
    Generate access token for a participant to join a room.
    
    Args:
        request: Room and participant information
        
    Returns:
        Access token, LiveKit URL, and room name
    """
    try:
        # Generate JWT token
        jwt_token = generate_access_token(request.room_name, request.participant_name)
        
        return TokenResponse(
            token=jwt_token,
            url=settings.livekit_url,
            room_name=request.room_name
        )
    
    except Exception as e:
        print(f"Error generating token: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate token: {str(e)}")
    
    
@router.get("/list-rooms")
async def list_rooms_router():
    """
    List all existing LiveKit rooms.
    
    Returns:
        List of rooms with their details
    """
    try:
        rooms_data = await list_rooms()
        return rooms_data
    
    except Exception as e:
        print(f"Error listing rooms: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list rooms: {str(e)}")