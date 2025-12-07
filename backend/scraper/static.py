"""Fast static scraping: httpx + BeautifulSoup."""

__all__ = ["scrape_static"]

from datetime import datetime, timezone
from typing import Optional, Tuple

import httpx

from backend.config import STATIC_TIMEOUT, DEFAULT_HEADERS
from backend.models import ScrapeResult, Meta, ScrapeError, Interactions
from backend.scraper.parser import parse_html, extract_meta
from backend.scraper.utils import needs_js_rendering


async def scrape_static(url: str) -> Tuple[Optional[ScrapeResult], bool]:
    """
    Fast HTTP-based scraping with BeautifulSoup.
    Returns (ScrapeResult | None, needs_js_flag).
    """
    errors = []

    try:
        # Fetch HTML with httpx
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=STATIC_TIMEOUT, headers=DEFAULT_HEADERS
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
            final_url = str(response.url)
    except httpx.TimeoutException:
        errors.append(
            ScrapeError(
                message=f"Request timed out after {STATIC_TIMEOUT}s", phase="static"
            )
        )
        return None, True
    except httpx.HTTPStatusError as e:
        errors.append(
            ScrapeError(
                message=f"HTTP {e.response.status_code}: {e.response.reason_phrase}",
                phase="static",
            )
        )
        return None, False
    except Exception as e:
        errors.append(
            ScrapeError(message=f"HTTP request error: {str(e)}", phase="static")
        )
        return None, False

    # Check if JS rendering is needed
    try:
        requires_js = needs_js_rendering(html)
        if requires_js:
            return None, True

        # Extract metadata and parse HTML
        meta = extract_meta(html, final_url, strategy="static")
        sections = parse_html(html, final_url)

        # Create result
        return (
            ScrapeResult(
                url=final_url,
                scrapedAt=datetime.now(timezone.utc).isoformat(),
                meta=meta,
                sections=sections,
                interactions=Interactions(clicks=[], scrolls=0, pages=[final_url]),
                errors=errors,
            ),
            False,
        )

    except Exception as e:
        errors.append(
            ScrapeError(message=f"HTML parsing error: {str(e)}", phase="parsing")
        )
        return None, False
