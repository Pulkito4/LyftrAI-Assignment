"""Playwright-based scraping for JS-rendered pages."""

__all__ = ["scrape_dynamic"]

import asyncio
from datetime import datetime, timezone
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
    Playwright-based scraping for JS-heavy sites.
    Launches headless Chrome, waits for content, optionally handles interactions.

    Args:
        url: Target URL
        enable_interactions: Enable depth ≥ 3 interactions
        interaction_strategy: Interaction mode ('auto', 'tabs', 'load_more', 'scroll', 'pagination', 'all')

    Returns:
        ScrapeResult or None if failed
    """
    errors = []
    pages_visited = []

    browser: Optional[Browser] = None

    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
                user_agent=USER_AGENT,
            )
            page = await context.new_page()

            # Navigate to URL
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
                pages_visited.append(page.url)

            # Wait strategy: best effort, continue on timeout
            try:
                await page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT)
            except PlaywrightTimeout:
                pass

            try:
                await page.wait_for_selector("body", timeout=NETWORK_IDLE_TIMEOUT)
                for selector in MAIN_CONTENT_SELECTORS:
                    try:
                        await page.wait_for_selector(selector, timeout=SELECTOR_WAIT_TIMEOUT)
                        break
                    except PlaywrightTimeout:
                        continue
            except PlaywrightTimeout:
                pass

            await asyncio.sleep(1)

            # Handle interactions if enabled
            interaction_results = await handle_interactions(page, strategy=interaction_strategy) if enable_interactions else {}
            pages_visited = interaction_results.get("pages", [page.url])
            html_contents = interaction_results.get("html_contents", [])

            # Extract rendered HTML
            html = await page.content()
            final_url = page.url

            # Close browser
            await browser.close()
            browser = None

        # Extract metadata and parse HTML - let errors bubble up
        meta = extract_meta(html, final_url, strategy="js")
        sections = []

        # Parse HTML sections
        if enable_interactions and html_contents:
            for i, page_html in enumerate(html_contents):
                page_url = pages_visited[i] if i < len(pages_visited) else final_url
                page_sections = parse_html(page_html, page_url)
                for section in page_sections:
                    section.id = f"{section.id}-p{i}"
                sections.extend(page_sections)
        else:
            sections = parse_html(html, final_url)

        # Build result
        interactions = Interactions(
            clicks=interaction_results.get("clicks", []),
            scrolls=interaction_results.get("scrolls", 0),
            pages=pages_visited,
        )

        return ScrapeResult(
            url=final_url,
            scrapedAt=datetime.now(timezone.utc).isoformat(),
            meta=meta,
            sections=sections,
            interactions=interactions,
            errors=errors,
        )

    except Exception as e:
        errors.append(
            ScrapeError(
                message=f"Dynamic scraping error: {str(e)}", phase="dynamic"
            )
        )
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
        return None
