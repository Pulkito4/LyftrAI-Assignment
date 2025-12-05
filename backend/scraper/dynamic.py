"""
Dynamic scraping using Playwright for JavaScript-rendered pages
"""
from typing import Optional
from datetime import datetime
import asyncio

from playwright.async_api import async_playwright, Browser, TimeoutError as PlaywrightTimeout

from backend.models import ScrapeResult, Meta, ScrapeError, Interactions
from backend.scraper.parser import parse_html
from backend.scraper.static import extract_meta
from backend.scraper.interactions import handle_interactions


# Timeouts for Playwright operations
PLAYWRIGHT_TIMEOUT = 30000  # 30 seconds for page load
PLAYWRIGHT_WAIT_TIMEOUT = 5000  # 5 seconds for wait operations


async def scrape_dynamic(
    url: str, 
    interactions_data: Optional[Interactions] = None,
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
        interactions_data: Optional Interactions object from previous steps
        enable_interactions: Whether to handle interactions (clicks, scrolls, pagination)
        interaction_strategy: Strategy for interactions ('auto', 'tabs', 'load_more', 'scroll', 'pagination', 'all')
    
    Returns:
        ScrapeResult or None if failed
    """
    errors = []
    pages_visited = [url]
    
    if interactions_data:
        pages_visited = interactions_data.pages
    
    browser: Optional[Browser] = None
    
    try:
        async with async_playwright() as p:
            # Launch browser
            try:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = await context.new_page()
            except Exception as e:
                errors.append(ScrapeError(
                    message=f"Failed to launch browser: {str(e)}",
                    phase="dynamic"
                ))
                return None
            
            # Navigate to URL
            try:
                response = await page.goto(url, wait_until='domcontentloaded', timeout=PLAYWRIGHT_TIMEOUT)
                
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
                    message=f"Page load timed out after {PLAYWRIGHT_TIMEOUT/1000}s",
                    phase="dynamic"
                ))
                # Continue anyway - partial content may be useful
            except Exception as e:
                errors.append(ScrapeError(
                    message=f"Navigation failed: {str(e)}",
                    phase="dynamic"
                ))
                if browser:
                    await browser.close()
                return None
            
            # Wait strategy: Multiple approaches
            try:
                # 1. Wait for network to be idle
                await page.wait_for_load_state('networkidle', timeout=PLAYWRIGHT_WAIT_TIMEOUT)
            except PlaywrightTimeout:
                pass  # Continue - not critical
            
            try:
                # 2. Wait for common content selectors
                await page.wait_for_selector('body', timeout=PLAYWRIGHT_WAIT_TIMEOUT)
                
                # Try to wait for main content areas
                selectors_to_try = ['main', 'article', '[role="main"]', '#content', '.content']
                for selector in selectors_to_try:
                    try:
                        await page.wait_for_selector(selector, timeout=2000)
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
            interactions = interactions_data or Interactions(
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
        
        # Try to close browser if still open
        if browser:
            try:
                await browser.close()
            except:
                pass
        
        return None


def scrape_dynamic_sync(
    url: str, 
    interactions_data: Optional[Interactions] = None,
    enable_interactions: bool = False,
    interaction_strategy: str = 'auto'
) -> Optional[ScrapeResult]:
    """
    Synchronous wrapper for dynamic scraping.
    """
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        scrape_dynamic(url, interactions_data, enable_interactions, interaction_strategy)
    )
