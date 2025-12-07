"""
Scraper package initialization.
Exposes main scraping functions and utilities.
"""

from backend.scraper.dynamic import scrape_dynamic
from backend.scraper.interactions import handle_interactions, normalize_url
from backend.scraper.parser import extract_meta, parse_html
from backend.scraper.scraper import scrape_url
from backend.scraper.static import scrape_static
from backend.scraper.utils import check_robots_txt, needs_js_rendering, validate_url

__all__ = [
    "scrape_url",
    "scrape_static",
    "scrape_dynamic",
    "parse_html",
    "extract_meta",
    "handle_interactions",
    "normalize_url",
    "validate_url",
    "check_robots_txt",
    "needs_js_rendering",
]
