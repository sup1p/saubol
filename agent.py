#!/usr/bin/env python3

"""
LiveKit Transcription Agent Entry Point

This script starts a LiveKit Agent for real-time audio transcription
using the OpenAI Whisper STT plugin.

Usage:
    python agent.py start

Requirements:
    - LIVEKIT_URL environment variable
    - LIVEKIT_API_KEY environment variable  
    - LIVEKIT_API_SECRET environment variable
    - OPENAI_API_KEY environment variable
"""

import logging
from livekit.agents import cli
from src.services.transcription import create_worker

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create and run the worker
    cli.run_app(create_worker())