"""
Scraper package initialization.
Exposes main scraping functions and utilities.
"""

from backend.scraper.scraper import scrape_url
from backend.scraper.parser import parse_html
from backend.scraper.static import scrape_static
from backend.scraper.dynamic import scrape_dynamic
from backend.scraper.interactions import handle_interactions
from backend.scraper.utils import validate_url, needs_js_rendering

__all__ = [
    "scrape_url",
    "parse_html",
    "scrape_static",
    "scrape_dynamic",
    "handle_interactions",
    "validate_url",
    "needs_js_rendering",
]
