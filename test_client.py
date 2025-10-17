"""
Simple test client to verify LiveKit room connection and transcription agent
"""
import asyncio
import os
from livekit import api, rtc
from src.core.settings import settings

async def test_room_connection():
    """Test connecting to a LiveKit room as a participant."""
    
    room_name = "omar"  # Same room name as in your test
    
    # Create room instance
    room = rtc.Room()
    
    # Generate access token for test participant
    token = api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
    token.with_identity("test-participant")
    token.with_grants(api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
    ))
    
    try:
        # Connect to room
        print(f"Connecting to room: {room_name}")
        await room.connect(settings.livekit_url, token.to_jwt())
        print(f"Connected successfully!")
        
        # Log room information
        print(f"Local participant: {room.local_participant.identity}")
        print(f"Remote participants: {len(room.remote_participants)}")
        
        for participant in room.remote_participants.values():
            print(f"  - {participant.identity} (tracks: {len(participant.track_publications)})")
        
        # Wait a bit to see if any agents connect
        print("Waiting for 10 seconds to observe room activity...")
        await asyncio.sleep(10)
        
        # Check again for new participants (transcription agents)
        print(f"After waiting - Remote participants: {len(room.remote_participants)}")
        for participant in room.remote_participants.values():
            print(f"  - {participant.identity} (tracks: {len(participant.track_publications)})")
        
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        await room.disconnect()
        print("Disconnected from room")

if __name__ == "__main__":
    asyncio.run(test_room_connection())