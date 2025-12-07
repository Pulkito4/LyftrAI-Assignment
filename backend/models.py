"""
Pydantic models for scraping API - strict adherence to assignment specification
"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field


class Meta(BaseModel):
    """Metadata about the scraped page"""

    title: str
    description: str
    language: str
    canonical: Optional[str] = None
    strategy: Optional[str] = None  # "static" or "js" to indicate scraping method


class LinkItem(BaseModel):
    """Individual link with text and href"""

    text: str
    href: str


class ImageItem(BaseModel):
    """Individual image with src and alt text"""

    src: str
    alt: str


class Content(BaseModel):
    """Content extracted from a section"""

    headings: List[str] = Field(default_factory=list)
    text: str = ""
    links: List[LinkItem] = Field(default_factory=list)
    images: List[ImageItem] = Field(default_factory=list)
    lists: List[List[str]] = Field(default_factory=list)  # Nested list structure
    tables: List[Any] = Field(default_factory=list)


class Section(BaseModel):
    """A parsed section of content from the page"""

    id: str  # e.g., 'hero-0', 'section-1', 'nav-0'
    type: str  # Allowed: 'hero', 'pricing', 'section', 'nav', 'footer', 'list', 'grid', 'faq', 'unknown'
    label: str  # Human-readable label
    sourceUrl: str  # URL this section came from
    content: Content
    rawHtml: str  # Truncated HTML snippet
    truncated: bool


class Interactions(BaseModel):
    """Tracks interactions during scraping"""

    clicks: List[str] = Field(default_factory=list)  # Selectors or descriptions
    scrolls: int = 0  # Number of scroll actions
    pages: List[str] = Field(default_factory=list)  # List of visited URLs


class ScrapeError(BaseModel):
    """Error that occurred during scraping"""

    message: str
    phase: str  # e.g., 'static', 'dynamic', 'parsing', 'interaction'


class ScrapeResult(BaseModel):
    """Root response object for scraping API"""

    url: str
    scrapedAt: str  # ISO8601 datetime
    meta: Meta
    sections: List[Section] = Field(default_factory=list)
    interactions: Interactions = Field(default_factory=Interactions)
    errors: List[ScrapeError] = Field(default_factory=list)


class ScrapeRequest(BaseModel):
    """Request body for POST /scrape"""

    url: str


class ScrapeRequestExtended(ScrapeRequest):
    """
    Extended scrape request with interaction options.

    Attributes:
        url: Target URL to scrape (inherited from ScrapeRequest)
        enable_interactions: Whether to handle user interactions
        interaction_strategy: Strategy for handling interactions
    """

    enable_interactions: bool = Field(
        default=False,
        description="Enable interaction handling (clicks, scrolls, pagination)",
    )
    interaction_strategy: str = Field(
        default="auto",
        description="Interaction strategy: 'auto', 'tabs', 'load_more', 'scroll', 'pagination', 'all'",
    )
