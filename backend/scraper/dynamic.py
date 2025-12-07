"""
Dynamic scraping using Playwright for JavaScript-rendered pages
"""
import asyncio
from datetime import datetime
from typing import Optional

from playwright.async_api import async_playwright, Browser, TimeoutError as PlaywrightTimeout

from backend.config import (
    PAGE_LOAD_TIMEOUT, 
    NETWORK_IDLE_TIMEOUT, 
    USER_AGENT, 
    SELECTOR_WAIT_TIMEOUT, 
    VIEWPORT_WIDTH, 
    VIEWPORT_HEIGHT,
    MAIN_CONTENT_SELECTORS,
)
from backend.models import ScrapeResult, Meta, ScrapeError, Interactions
from backend.scraper.interactions import handle_interactions
from backend.scraper.parser import parse_html, extract_meta


async def scrape_dynamic(
    url: str,
    enable_interactions: bool = False,
    interaction_strategy: str = 'auto'
) -> Optional[ScrapeResult]:
    """
    Perform dynamic scraping using Playwright.
    
    This handles JavaScript-rendered content by:
    1. Launching a headless browser
    2. Navigating to the URL
    3. Waiting for content to load (network idle + selectors)
    4. Optionally handling interactions (tabs, load more, scroll, pagination)
    5. Extracting the rendered HTML
    6. Parsing with the unified parser
    
    Args:
        url: The URL to scrape
        enable_interactions: Whether to handle interactions (clicks, scrolls, pagination)
        interaction_strategy: Strategy for interactions ('auto', 'tabs', 'load_more', 'scroll', 'pagination', 'all')
    
    Returns:
        ScrapeResult or None if failed
    """
    errors = []
    pages_visited = [url]
    
    browser: Optional[Browser] = None
    
    try:
        async with async_playwright() as p:
            # Launch browser
            try:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': VIEWPORT_WIDTH, 'height': VIEWPORT_HEIGHT},
                    user_agent=USER_AGENT
                )
                page = await context.new_page()
            except Exception as e:
                errors.append(ScrapeError(
                    message=f"Failed to launch browser: {str(e)}",
                    phase="dynamic"
                ))
                return None
            
            try:
                response = await page.goto(url, wait_until='domcontentloaded', timeout=PAGE_LOAD_TIMEOUT)
                
                if response and not response.ok:
                    errors.append(ScrapeError(
                        message=f"HTTP {response.status}: Page load failed",
                        phase="dynamic"
                    ))
                
                final_url = page.url
                if final_url != url:
                    pages_visited.append(final_url)
                
            except PlaywrightTimeout:
                errors.append(ScrapeError(
                    message=f"Page load timed out after {PAGE_LOAD_TIMEOUT/1000}s",
                    phase="dynamic"
                ))
                # Continue anyway - partial content may be useful
            except Exception as e:
                errors.append(ScrapeError(
                    message=f"Navigation failed: {str(e)}",
                    phase="dynamic"
                ))
                try:
                    await browser.close()
                except Exception:
                    pass
                return None
            
            # Wait strategy: Multiple approaches
            try:
                # 1. Wait for network to be idle
                await page.wait_for_load_state('networkidle', timeout=NETWORK_IDLE_TIMEOUT)
            except PlaywrightTimeout:
                pass  # Continue - not critical
            
            try:
                # 2. Wait for common content selectors
                await page.wait_for_selector('body', timeout=NETWORK_IDLE_TIMEOUT)
                
                # Try to wait for main content areas
                for selector in MAIN_CONTENT_SELECTORS:
                    try:
                        await page.wait_for_selector(selector, timeout=SELECTOR_WAIT_TIMEOUT)
                        break
                    except PlaywrightTimeout:
                        continue
            except PlaywrightTimeout:
                pass  # Continue anyway
            
            # Small delay for any remaining dynamic content
            await asyncio.sleep(1)
            
            # Handle interactions if enabled
            interaction_results = {'clicks': [], 'scrolls': 0, 'pages': pages_visited.copy()}
            
            if enable_interactions:
                try:
                    interaction_results = await handle_interactions(page, strategy=interaction_strategy)
                    
                    # Update pages visited
                    for page_url in interaction_results['pages']:
                        if page_url not in pages_visited:
                            pages_visited.append(page_url)
                    
                except Exception as e:
                    errors.append(ScrapeError(
                        message=f"Interaction handling failed: {str(e)}",
                        phase="interaction"
                    ))
            
            # Get the rendered HTML (after interactions)
            try:
                html = await page.content()
                final_url = page.url
            except Exception as e:
                errors.append(ScrapeError(
                    message=f"Failed to extract HTML: {str(e)}",
                    phase="dynamic"
                ))
                if browser:
                    await browser.close()
                return None
            
            # Close browser
            await browser.close()
            browser = None
        
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
        
        # Build interactions object
        if enable_interactions:
            interactions = Interactions(
                clicks=interaction_results.get('clicks', []),
                scrolls=interaction_results.get('scrolls', 0),
                pages=pages_visited
            )
        else:
            interactions = Interactions(
                clicks=[],
                scrolls=0,
                pages=pages_visited
            )
        
        # Create result
        result = ScrapeResult(
            url=final_url,
            scrapedAt=datetime.utcnow().isoformat() + "Z",
            meta=meta,
            sections=sections,
            interactions=interactions,
            errors=errors
        )
        
        return result
        
    except Exception as e:
        errors.append(ScrapeError(
            message=f"Unexpected error in dynamic scraping: {str(e)}",
            phase="dynamic"
        ))
        
        try:
            await browser.close()
        except Exception:
            pass
        
        return None
