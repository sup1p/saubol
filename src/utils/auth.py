"""
Authentication and token utilities for LiveKit
"""
import base64
import hashlib
import hmac
import time
import requests
import jwt
from livekit import api
from src.core.settings import settings


def create_room_auth_token() -> str:
    """Create JWT token for room creation authentication"""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": settings.livekit_api_key,
        "exp": int(time.time()) + 3600,  # 1 hour
        "video": {
            "roomCreate": True
        }
    }
    
    return jwt.encode(payload, settings.livekit_api_secret, algorithm="HS256", headers=header)


async def create_room(room_name: str) -> dict:
    """
    Create a room using HTTP request to LiveKit server
    
    Args:
        room_name: Name for the new room
        
    Returns:
        Room creation response data
    """
    token = create_room_auth_token()
    
    # Make HTTP request to create room
    url = f"https://{settings.livekit_url.replace('wss://', '').replace('ws://', '')}/twirp/livekit.RoomService/CreateRoom"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"name": room_name, "empty_timeout": 15, "max_participants": 10}
    
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    
    return response.json()


def generate_access_token(room_name: str, participant_name: str) -> str:
    """
    Generate access token for a participant to join a room
    
    Args:
        room_name: Name of the room
        participant_name: Name of the participant
        
    Returns:
        JWT access token
    """
    token = api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
    token.with_identity(participant_name)
    token.with_name(participant_name)
    token.with_grants(
        api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True
        )
    )
    
    return token.to_jwt()