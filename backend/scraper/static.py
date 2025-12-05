"""
Static scraping using httpx and HTML parser
"""
import httpx
from typing import Tuple, Optional
from datetime import datetime

from backend.models import ScrapeResult, Meta, ScrapeError, Interactions
from backend.scraper.parser import parse_html
from backend.scraper.utils import validate_url, needs_js_rendering, get_content_length
from bs4 import BeautifulSoup


# Timeout for static HTTP requests
STATIC_TIMEOUT = 10.0


def extract_meta(html: str, url: str) -> Meta:
    """
    Extract metadata from HTML (title, description, language, canonical).
    """
    soup = BeautifulSoup(html, 'lxml')
    
    # Title - try multiple sources
    title = ""
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)
    
    # Try og:title if no title
    if not title:
        og_title = soup.find('meta', property='og:title')
        if og_title:
            title = og_title.get('content', '').strip()
    
    if not title:
        title = "Untitled"
    
    # Description
    description = ""
    desc_tag = soup.find('meta', attrs={'name': 'description'})
    if desc_tag:
        description = desc_tag.get('content', '').strip()
    
    # Try og:description
    if not description:
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            description = og_desc.get('content', '').strip()
    
    if not description:
        description = ""
    
    # Language - from html lang attribute
    language = "en"  # Default
    html_tag = soup.find('html')
    if html_tag and html_tag.get('lang'):
        language = html_tag.get('lang', 'en').strip().split('-')[0]  # Get base language
    
    # Canonical URL
    canonical = None
    canonical_tag = soup.find('link', rel='canonical')
    if canonical_tag and canonical_tag.get('href'):
        canonical = canonical_tag.get('href').strip()
    
    return Meta(
        title=title,
        description=description,
        language=language,
        canonical=canonical
    )


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
    
    # Validate URL
    is_valid, error_msg = validate_url(url)
    if not is_valid:
        errors.append(ScrapeError(message=error_msg, phase="validation"))
        return None, False
    
    try:
        # Fetch HTML with httpx
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        async with httpx.AsyncClient(follow_redirects=True, timeout=STATIC_TIMEOUT, headers=headers) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text
                final_url = str(response.url)
            except httpx.TimeoutException:
                errors.append(ScrapeError(
                    message=f"Request timed out after {STATIC_TIMEOUT}s",
                    phase="static"
                ))
                return None, True  # Might work with JS rendering
            except httpx.HTTPStatusError as e:
                errors.append(ScrapeError(
                    message=f"HTTP {e.response.status_code}: {e.response.reason_phrase}",
                    phase="static"
                ))
                return None, False
            except Exception as e:
                errors.append(ScrapeError(
                    message=f"Request failed: {str(e)}",
                    phase="static"
                ))
                return None, False
        
        # Check if JS rendering is needed
        requires_js = needs_js_rendering(html)
        content_length = get_content_length(html)
        
        if requires_js:
            # Return partial result indicating JS is needed
            return None, True
        
        # Extract metadata
        try:
            meta = extract_meta(html, final_url)
        except Exception as e:
            errors.append(ScrapeError(
                message=f"Failed to extract metadata: {str(e)}",
                phase="parsing"
            ))
            meta = Meta(title="Error", description="", language="en", canonical=None)
        
        # Parse HTML into sections
        try:
            sections = parse_html(html, final_url)
        except Exception as e:
            errors.append(ScrapeError(
                message=f"Failed to parse HTML: {str(e)}",
                phase="parsing"
            ))
            sections = []
        
        # Create result
        result = ScrapeResult(
            url=final_url,
            scrapedAt=datetime.utcnow().isoformat() + "Z",
            meta=meta,
            sections=sections,
            interactions=Interactions(
                clicks=[],
                scrolls=0,
                pages=[final_url]
            ),
            errors=errors
        )
        
        return result, False
        
    except Exception as e:
        errors.append(ScrapeError(
            message=f"Unexpected error in static scraping: {str(e)}",
            phase="static"
        ))
        return None, False


def scrape_static_sync(url: str) -> Tuple[Optional[ScrapeResult], bool]:
    """
    Synchronous wrapper for static scraping.
    Used when async context is not available.
    """
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(scrape_static(url))
