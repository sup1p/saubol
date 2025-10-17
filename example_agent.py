"""
Example script demonstrating how to use the LiveKit Transcription Agent

This example shows how to programmatically start the transcription agent
for a specific room.
"""

import asyncio
import os
from livekit.agents import Worker
from src.services.transcription import create_worker

async def main():
    """Start the transcription agent worker."""
    
    # Ensure required environment variables are set
    required_vars = [
        "LIVEKIT_URL", 
        "LIVEKIT_API_KEY", 
        "LIVEKIT_API_SECRET", 
        "OPENAI_API_KEY"
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            print(f"Error: {var} environment variable not set")
            return
    
    # Create worker with our transcription agent
    worker_options = create_worker()
    worker = Worker(worker_options)
    
    print("Starting LiveKit Transcription Agent...")
    print(f"Connecting to: {os.getenv('LIVEKIT_URL')}")
    
    # Start the worker (this will block)
    await worker.start()

if __name__ == "__main__":
    asyncio.run(main())