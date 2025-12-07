"""
Dynamic scraping using Playwright for JavaScript-rendered pages
"""

import asyncio
from datetime import datetime
from typing import Optional

from playwright.async_api import (
    async_playwright,
    Browser,
    TimeoutError as PlaywrightTimeout,
)

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
    url: str, enable_interactions: bool = False, interaction_strategy: str = "auto"
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
    pages_visited = []

    browser: Optional[Browser] = None

    try:
        async with async_playwright() as p:
            # Launch browser
            try:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
                    user_agent=USER_AGENT,
                )
                page = await context.new_page()
            except Exception as e:
                errors.append(
                    ScrapeError(
                        message=f"Failed to launch browser: {str(e)}", phase="dynamic"
                    )
                )
                return None

            try:
                response = await page.goto(
                    url, wait_until="domcontentloaded", timeout=PAGE_LOAD_TIMEOUT
                )

                if response and not response.ok:
                    errors.append(
                        ScrapeError(
                            message=f"HTTP {response.status}: Page load failed",
                            phase="dynamic",
                    )
                )

                pages_visited.append(page.url)

            except PlaywrightTimeout:
                errors.append(
                    ScrapeError(
                        message=f"Page load timed out after {PAGE_LOAD_TIMEOUT / 1000}s",
                        phase="dynamic",
                    )
                )
                # Continue anyway - partial content may be useful
            except Exception as e:
                errors.append(
                    ScrapeError(message=f"Navigation failed: {str(e)}", phase="dynamic")
                )
                try:
                    await browser.close()
                except Exception:
                    pass
                return None

            # Wait strategy: Multiple approaches
            try:
                # 1. Wait for network to be idle
                await page.wait_for_load_state(
                    "networkidle", timeout=NETWORK_IDLE_TIMEOUT
                )
            except PlaywrightTimeout:
                pass  # Continue - not critical

            try:
                # 2. Wait for common content selectors
                await page.wait_for_selector("body", timeout=NETWORK_IDLE_TIMEOUT)

                # Try to wait for main content areas
                for selector in MAIN_CONTENT_SELECTORS:
                    try:
                        await page.wait_for_selector(
                            selector, timeout=SELECTOR_WAIT_TIMEOUT
                        )
                        break
                    except PlaywrightTimeout:
                        continue
            except PlaywrightTimeout:
                pass  # Continue anyway

            # Small delay for any remaining dynamic content
            await asyncio.sleep(1)

            # Initialize interaction variables
            interaction_results = {}
            html_contents = []

            # Handle interactions if enabled
            if enable_interactions:
                try:
                    interaction_results = await handle_interactions(
                        page, strategy=interaction_strategy
                    )
                    pages_visited = interaction_results.get("pages", [page.url])
                    html_contents = interaction_results.get("html_contents", [])

                except Exception as e:
                    errors.append(
                        ScrapeError(
                            message=f"Interaction handling failed: {str(e)}",
                            phase="interaction",
                        )
                    )
                    pages_visited = [page.url]
            else:
                pages_visited = [page.url]

            # Get the rendered HTML (after interactions)
            try:
                html = await page.content()
                final_url = page.url
            except Exception as e:
                errors.append(
                    ScrapeError(
                        message=f"Failed to extract HTML: {str(e)}", phase="dynamic"
                    )
                )
                if browser:
                    await browser.close()
                return None

            # Close browser
            await browser.close()
            browser = None

        # Extract metadata from final page
        try:
            meta = extract_meta(html, final_url)
        except Exception as e:
            errors.append(
                ScrapeError(
                    message=f"Failed to extract metadata: {str(e)}", phase="parsing"
                )
            )
            meta = Meta(title="Error", description="", language="en", canonical=None)

        # Parse HTML into sections
        sections = []
        
        # If we have multiple HTML contents from pagination, parse all of them
        if enable_interactions and html_contents:
            try:
                for i, page_html in enumerate(html_contents):
                    page_url = pages_visited[i] if i < len(pages_visited) else final_url
                    page_sections = parse_html(page_html, page_url)
                    sections.extend(page_sections)
            except Exception as e:
                errors.append(
                    ScrapeError(message=f"Failed to parse paginated HTML: {str(e)}", phase="parsing")
                )
        else:
            # Single page - parse the current HTML
            try:
                sections = parse_html(html, final_url)
            except Exception as e:
                errors.append(
                    ScrapeError(message=f"Failed to parse HTML: {str(e)}", phase="parsing")
                )
                sections = []

        # Build interactions object
        if enable_interactions:
            interactions = Interactions(
                clicks=interaction_results.get("clicks", []),
                scrolls=interaction_results.get("scrolls", 0),
                pages=pages_visited,
            )
        else:
            interactions = Interactions(clicks=[], scrolls=0, pages=pages_visited)

        # Create result
        result = ScrapeResult(
            url=final_url,
            scrapedAt=datetime.utcnow().isoformat() + "Z",
            meta=meta,
            sections=sections,
            interactions=interactions,
            errors=errors,
        )

        return result

    except Exception as e:
        errors.append(
            ScrapeError(
                message=f"Unexpected error in dynamic scraping: {str(e)}",
                phase="dynamic",
            )
        )

        try:
            await browser.close()
        except Exception:
            pass

        return None
