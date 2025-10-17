"""
FastAPI dependencies for dependency injection
"""
from .settings import settings


def get_settings():
    """Get application settings"""
    return settings