"""
Interaction handling - clicks, scrolls, and pagination for depth >= 3
"""

import asyncio
from typing import List, Tuple

from playwright.async_api import (
    Page,
    TimeoutError as PlaywrightTimeout,
    Error as PlaywrightError,
)

from backend.config import (
    MAX_INTERACTION_DEPTH as MAX_DEPTH,
    NETWORK_IDLE_TIMEOUT as INTERACTION_TIMEOUT,
    INTERACTIVE_SELECTORS,
)

# Extract selectors from config
TAB_SELECTORS = INTERACTIVE_SELECTORS["tabs"]
LOAD_MORE_SELECTORS = INTERACTIVE_SELECTORS["load_more"]
PAGINATION_SELECTORS = INTERACTIVE_SELECTORS["pagination"]


async def try_click_tabs(page: Page) -> List[str]:
    """
    Attempt to click tabs to reveal additional content.

    Returns:
        List of descriptions of clicked tabs
    """
    clicks = []

    # Try to find tab containers
    for selector in TAB_SELECTORS:
        try:
            tabs = await page.query_selector_all(selector)

            if len(tabs) == 0:
                continue

            for tab in tabs[:MAX_DEPTH]:
                try:
                    # Just try to click - if not visible/enabled, will fail naturally
                    text = (await tab.inner_text()).strip()[:50]
                    await tab.click(timeout=INTERACTION_TIMEOUT)
                    clicks.append(f"Tab clicked: {selector} - {text}")
                    await asyncio.sleep(0.5)
                except (PlaywrightTimeout, PlaywrightError, AttributeError):
                    continue

            if clicks:
                break

        except (PlaywrightTimeout, PlaywrightError):
            continue

    return clicks


async def try_click_load_more(
    page: Page, max_clicks: int = MAX_DEPTH
) -> Tuple[List[str], int]:
    """
    Attempt to click "Load more" or "Show more" buttons repeatedly.

    Args:
        page: Playwright page
        max_clicks: Maximum number of times to click

    Returns:
        (clicks_list, actual_clicks_count)
    """
    clicks = []
    click_count = 0

    for attempt in range(max_clicks):
        clicked = False

        for selector in LOAD_MORE_SELECTORS:
            try:
                button = await page.query_selector(selector)
                text = (await button.inner_text()).strip()[:50]
                len_before = len(await page.content())

                await button.click(timeout=INTERACTION_TIMEOUT)
                clicks.append(f"Load more clicked ({attempt + 1}): {text}")
                click_count += 1
                clicked = True

                await asyncio.sleep(2)

                # Check if content actually changed
                if len(await page.content()) <= len_before:
                    return clicks, click_count

                break
            except (PlaywrightTimeout, PlaywrightError, AttributeError, TypeError):
                continue

        if not clicked:
            break

    return clicks, click_count


async def try_infinite_scroll(page: Page, max_scrolls: int = MAX_DEPTH) -> int:
    """
    Perform infinite scroll by scrolling down and waiting for content to load.

    Args:
        page: Playwright page
        max_scrolls: Maximum number of scroll operations

    Returns:
        Number of successful scrolls
    """
    scroll_count = 0

    for attempt in range(max_scrolls):
        try:
            # Get current scroll height before scrolling
            height_before = await page.evaluate("() => document.body.scrollHeight")

            # Scroll to bottom
            await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            scroll_count += 1

            # Wait for new content to load
            await asyncio.sleep(2)

            # Optional: Wait for network to be idle
            try:
                await page.wait_for_load_state(
                    "networkidle", timeout=INTERACTION_TIMEOUT
                )
            except PlaywrightTimeout:
                pass

            # Check if height changed after scrolling
            height_after = await page.evaluate("() => document.body.scrollHeight")
            
            # If height hasn't changed, no new content loaded
            if height_after <= height_before:
                break

        except (PlaywrightTimeout, PlaywrightError, Exception):
            break

    return scroll_count


async def try_pagination(
    page: Page, max_pages: int = MAX_DEPTH
) -> Tuple[List[str], int, List[str]]:
    """
    Follow pagination links up to max_pages.

    Args:
        page: Playwright page
        max_pages: Maximum number of pages to visit (including current)

    Returns:
        (pages_visited, pages_count, html_contents)
    """
    pages_visited = [page.url]
    html_contents = [await page.content()]
    pages_count = 1

    for attempt in range(max_pages - 1):
        clicked = False

        for selector in PAGINATION_SELECTORS:
            try:
                next_button = await page.query_selector(selector)
                url_before = page.url

                await next_button.click(timeout=INTERACTION_TIMEOUT)

                try:
                    await page.wait_for_load_state(
                        "domcontentloaded", timeout=INTERACTION_TIMEOUT
                    )
                except PlaywrightTimeout:
                    await asyncio.sleep(1)

                url_after = page.url
                if normalize_url(url_after) != normalize_url(url_before) and \
                   normalize_url(url_after) not in [normalize_url(u) for u in pages_visited]:
                    pages_visited.append(url_after)
                    html_contents.append(await page.content())
                    pages_count += 1
                    clicked = True
                    await asyncio.sleep(1)
                    break
            except (PlaywrightTimeout, PlaywrightError, AttributeError, TypeError):
                continue

        if not clicked:
            break

    return pages_visited, pages_count, html_contents


def normalize_url(url: str) -> str:
    """Normalize URL by removing trailing slash for comparison."""
    return url.rstrip('/')


async def handle_interactions(page: Page, strategy: str = "auto") -> dict:
    """
    Main interaction handler - orchestrates clicks, scrolls, and pagination.

    Args:
        page: Playwright page
        strategy: Interaction strategy
            - 'auto': Try to detect what's needed
            - 'tabs': Focus on clicking tabs
            - 'load_more': Focus on "load more" buttons
            - 'scroll': Focus on infinite scroll
            - 'pagination': Focus on pagination links
            - 'all': Try everything

    Returns:
        Dictionary with:
            - clicks: List[str] - Descriptions of clicked elements
            - scrolls: int - Number of scroll operations
            - pages: List[str] - URLs visited
            - html_contents: List[str] - HTML from each page (for pagination)
    """
    clicks = []
    scrolls = 0
    pages = [page.url]
    html_contents = []

    try:
        if strategy in ["auto", "tabs", "all"]:
            # Try clicking tabs first
            tab_clicks = await try_click_tabs(page)
            clicks.extend(tab_clicks)

        if strategy in ["auto", "load_more", "all"]:
            # Try "load more" buttons
            load_more_clicks, _ = await try_click_load_more(page, max_clicks=MAX_DEPTH)
            clicks.extend(load_more_clicks)

        if strategy in ["auto", "scroll", "all"]:
            # Try infinite scroll
            scroll_count = await try_infinite_scroll(page, max_scrolls=MAX_DEPTH)
            scrolls = scroll_count

        if strategy in ["auto", "pagination", "all"]:
            pagination_pages, _, pagination_html = await try_pagination(page, max_pages=MAX_DEPTH)
            # Replace pages with pagination results
            if pagination_pages:
                pages = pagination_pages
                html_contents = pagination_html

        # For 'auto' strategy, if nothing worked, try everything
        if strategy == "auto" and not clicks and scrolls == 0 and len(pages) == 1:
            # Try everything as fallback
            load_more_clicks, _ = await try_click_load_more(page, max_clicks=MAX_DEPTH)
            clicks.extend(load_more_clicks)

            scroll_count = await try_infinite_scroll(page, max_scrolls=MAX_DEPTH)
            scrolls = max(scrolls, scroll_count)

    except Exception:
        # Don't fail completely on interaction errors
        pass

    return {"clicks": clicks, "scrolls": scrolls, "pages": pages, "html_contents": html_contents}
