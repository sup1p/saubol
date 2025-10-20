"""
Application settings and configuration
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # LiveKit settings
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    
    # Whisper settings
    
    # OpenAI settings
    openai_api_key: str
    
    # FastAPI settings
    app_title: str = "Speech-to-Text with LiveKit"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # CORS settings
    allowed_origins: list = ["*"]
    
    
    livekit_agent_name: str = "transcription-agent"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()