"""
Real-time transcription service for LiveKit audio streams
"""
from src.core.settings import settings

from typing import Optional
from livekit import api, rtc
from scipy import signal
import soundfile as sf
from io import BytesIO
from datetime import datetime

import asyncio
import numpy as np
import openai



class TranscriptionSession:
    """
    Handles real-time audio transcription for a LiveKit room.
    Subscribes to audio tracks, buffers audio data, and transcribes using Whisper.
    """
    
    def __init__(self, room_name: str):
        """
        Initialize a transcription session for a specific room.
        
        Args:
            room_name: Name of the LiveKit room to join
        """
        self.room_name = room_name
        self.room = None
        self.audio_buffer = []
        self.is_running = False
        openai.api_key = settings.openai_api_key
    
    async def connect(self) -> None:
        """
        Connect to LiveKit room and set up event handlers for audio streaming.
        Creates a transcription agent that subscribes to all audio tracks.
        """
        self.room = rtc.Room()
        
        @self.room.on("track_subscribed")
        def on_track_subscribed(
            track: rtc.Track,
            publication: rtc.RemoteTrackPublication,
            participant: rtc.RemoteParticipant
        ):
            """Handle new audio track subscription"""
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                print(f"Subscribed to audio track from {participant.identity}")
                asyncio.create_task(self.process_audio_track(track))
        
        @self.room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            """Handle participant connection"""
            print(f"Participant connected: {participant.identity}")
            print(f"Participant has {len(participant.audioTracks)} audio tracks")
        
        @self.room.on("track_published")
        def on_track_published(publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
            """Handle track publication"""
            print(f"Track published: {publication.sid} by {participant.identity}, kind: {publication.kind}")
        
        # Generate token for transcription agent
        token = api.AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        token.with_identity("transcription-agent")
        token.with_grants(
            api.VideoGrants(
                room_join=True,
                room=self.room_name,
                can_subscribe=True
            )
        )
        
        # Connect to room
        await self.room.connect(settings.livekit_url, token.to_jwt())
        self.is_running = True
        print(f"Connected to room: {self.room_name}")
    
    async def process_audio_track(self, track: rtc.AudioTrack) -> None:
        """
        Process incoming audio stream from a track.
        Buffers audio frames and triggers transcription periodically.
        
        Args:
            track: The audio track to process
        """
        print(f"Starting to process audio track: {track.sid}")
        audio_stream = rtc.AudioStream(track)
        frame_count = 0
        
        async for frame in audio_stream:
            if not self.is_running:
                print("Audio processing stopped - session not running")
                break
            
            # Append frame to buffer
            self.audio_buffer.append(frame)
            frame_count += 1
            
            # Log every 10 frames to show audio is being received
            
            # Process buffer when we have approximately 10 seconds of audio
            # (500 frames at 50 frames/sec)
            if len(self.audio_buffer) >= 500:
                print(f"Buffer full ({len(self.audio_buffer)} frames), starting transcription...")
                await self.transcribe_buffer()
    
    async def transcribe_buffer(self) -> None:
        """
        Transcribe accumulated audio buffer using OpenAI Whisper API.
        Converts audio frames to numpy array and sends to OpenAI API.
        """
        if not self.audio_buffer:
            return
        
        try:
            # Convert frames to numpy array
            audio_data = self.frames_to_numpy(self.audio_buffer)
            
            print(f"OPENAI_API_KEY present: {bool(settings.openai_api_key)}")
            
            # Use OpenAI Whisper API
            print("Sending audio to OpenAI Whisper API...")
            
            # Prepare a temporary WAV file from numpy array
            buf = BytesIO()
            # Write as 16-bit PCM wav at 16kHz
            sf.write(buf, audio_data, 16000, format='WAV', subtype='PCM_16')
            buf.seek(0)
            print(f"Created WAV buffer of {buf.tell()} bytes")

            # Use OpenAI SDK
            buf.name = "audio.wav"  # Give it a filename for OpenAI SDK
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=buf,
                language="en"
            )
            
            text = transcript.text.strip()
            print(f"OpenAI transcription successful: '{text}'")
            
            if not text:
                print("Empty transcription result - audio might be too quiet or unclear")
                self.audio_buffer = []
                return
            
            if text:
                print(f"FINAL TRANSCRIPTION: {text}")
                # Send transcription back to room via data channel
                try:
                    # Create data payload with timestamp
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    message_with_timestamp = f"[{timestamp}] {text}"
                    
                    # For publish_data, we need bytes
                    data_payload_publishing = message_with_timestamp.encode('utf-8')
                    print(f"Sending data payload: {data_payload_publishing} (length: {len(data_payload_publishing)})")

                    # Send to all participants in the room
                    await self.room.local_participant.publish_data(data_payload_publishing, topic="transcription")
                    
                    # For send_text, we need string (not bytes)
                    await self.room.local_participant.send_text(message_with_timestamp, topic="lk.chat")
                    print(f"Data sent to room successfully: {text}")
                except Exception as e:
                    print(f"Failed to send transcription to room: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Clear buffer
            self.audio_buffer = []
            print("Buffer cleared")
        
        except Exception as e:
            print(f"Transcription error: {e}")
            self.audio_buffer = []
    
    def frames_to_numpy(self, frames) -> np.ndarray:
        """
        Convert audio frames to numpy array for Whisper processing.
        
        Args:
            frames: List of audio frames from LiveKit
            
        Returns:
            Normalized float32 numpy array suitable for Whisper
        """
        print(f"Processing {len(frames)} frames")
        
        # Extract audio data from frames
        audio_chunks = []
        for frame in frames:
            # Try different frame structures that LiveKit might use
            audio_data = None
            if hasattr(frame, 'data'):
                audio_data = frame.data
            elif hasattr(frame, 'frame') and hasattr(frame.frame, 'data'):
                audio_data = frame.frame.data
            else:
                print(f"Unexpected frame structure: {type(frame)}, attrs: {dir(frame)}")
                continue
            
            if audio_data:
                audio_chunks.append(audio_data)
            else:
                print(f"No audio data in frame: {frame}")
                continue
        
        if not audio_chunks:
            print("No audio data found in frames")
            return np.array([], dtype=np.float32)
        
        # Combine all audio frames
        audio_data = b''.join(audio_chunks)
        print(f"Combined audio data: {len(audio_data)} bytes")
        
        # Convert to numpy array (16-bit PCM)
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        print(f"Audio array shape: {audio_array.shape}, dtype: {audio_array.dtype}")
        
        # Normalize to [-1, 1] range (Whisper expects float32 normalized audio)
        audio_array = audio_array.astype(np.float32) / 32768.0
        
        # Resample from 48kHz to 16kHz for better Whisper compatibility
        # LiveKit typically provides 48kHz audio
        target_sample_rate = 16000
        current_sample_rate = 48000  # LiveKit standard is 48kHz
        audio_array = signal.resample(audio_array, int(len(audio_array) * target_sample_rate / current_sample_rate))
        print(f"Resampled audio shape: {audio_array.shape}")
        
        return audio_array
    
    async def disconnect(self) -> None:
        """
        Disconnect from LiveKit room and cleanup resources.
        """
        self.is_running = False
        if self.room:
            await self.room.disconnect()
        print(f"Disconnected from room: {self.room_name}")