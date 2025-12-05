"""
Backend package initialization.
Exposes main application and models for easy imports.
"""

from backend.main import app
from backend.models import (
    ScrapeResult,
    Meta,
    Section,
    Content,
    Interactions,
    ScrapeError,
)

__all__ = [
    "app",
    "ScrapeResult",
    "Meta",
    "Section",
    "Content",
    "Interactions",
    "ScrapeError",
]
