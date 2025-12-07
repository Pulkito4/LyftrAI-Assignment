"""
Backend package initialization.
Exposes main application and models for easy imports.
"""

from backend.main import app
from backend.models import (
    ScrapeResult,
    ScrapeRequest,
    ScrapeRequestExtended,
    Meta,
    Section,
    Content,
    LinkItem,
    ImageItem,
    Interactions,
    ScrapeError,
)

__all__ = [
    "app",
    "ScrapeResult",
    "ScrapeRequest",
    "ScrapeRequestExtended",
    "Meta",
    "Section",
    "Content",
    "LinkItem",
    "ImageItem",
    "Interactions",
    "ScrapeError",
]
