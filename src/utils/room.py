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


def create_room_list_token() -> str:
    """Create JWT token for room listing authentication"""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": settings.livekit_api_key,
        "exp": int(time.time()) + 3600,  # 1 hour
        "video": {
            "roomList": True
        }
    }
    
    return jwt.encode(payload, settings.livekit_api_secret, algorithm="HS256", headers=header)

async def list_rooms() -> dict:
    """
    Create a room using HTTP request to LiveKit server
    
    Args:
        room_name: Name for the new room
        
    Returns:
        Room creation response data
    """
    token = create_room_list_token()
    
    # Make HTTP request to create room
    url = f"https://{settings.livekit_url.replace('wss://', '').replace('ws://', '')}/twirp/livekit.RoomService/ListRooms"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {}
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    return data