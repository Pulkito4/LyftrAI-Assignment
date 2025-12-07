"""
Static scraping using httpx and HTML parser
"""

from datetime import datetime
from typing import Optional, Tuple

import httpx

from backend.config import STATIC_TIMEOUT, DEFAULT_HEADERS
from backend.models import ScrapeResult, Meta, ScrapeError, Interactions
from backend.scraper.parser import parse_html, extract_meta
from backend.scraper.utils import needs_js_rendering


async def scrape_static(url: str) -> Tuple[Optional[ScrapeResult], bool]:
    """
    Perform static scraping using httpx.

    Returns:
        (result, needs_js) where:
        - result: ScrapeResult if successful, None if failed
        - needs_js: True if JS rendering is recommended

    The result may contain errors in the errors[] field.
    """
    errors = []

    try:
        # Fetch HTML with httpx
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=STATIC_TIMEOUT, headers=DEFAULT_HEADERS
        ) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text
                final_url = str(response.url)
            except httpx.TimeoutException:
                errors.append(
                    ScrapeError(
                        message=f"Request timed out after {STATIC_TIMEOUT}s",
                        phase="static",
                    )
                )
                return None, True  # Might work with JS rendering
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
                    ScrapeError(message=f"Request failed: {str(e)}", phase="static")
                )
                return None, False

        # Check if JS rendering is needed
        requires_js = needs_js_rendering(html)

        if requires_js:
            # Return partial result indicating JS is needed
            return None, True

        # Extract metadata
        try:
            meta = extract_meta(html, final_url, strategy="static")
        except Exception as e:
            errors.append(
                ScrapeError(
                    message=f"Failed to extract metadata: {str(e)}", phase="parsing"
                )
            )
            meta = Meta(title="Error", description="", language="en", canonical=None, strategy="static")

        # Parse HTML into sections
        try:
            sections = parse_html(html, final_url)
        except Exception as e:
            errors.append(
                ScrapeError(message=f"Failed to parse HTML: {str(e)}", phase="parsing")
            )
            sections = []

        # Create result
        result = ScrapeResult(
            url=final_url,
            scrapedAt=datetime.utcnow().isoformat() + "Z",
            meta=meta,
            sections=sections,
            interactions=Interactions(clicks=[], scrolls=0, pages=[final_url]),
            errors=errors,
        )

        return result, False

    except Exception as e:
        errors.append(
            ScrapeError(
                message=f"Unexpected error in static scraping: {str(e)}", phase="static"
            )
        )
        return None, False
