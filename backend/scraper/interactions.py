"""Depth ≥ 3 interaction handlers: tabs, load more, scroll, pagination."""

__all__ = ["handle_interactions", "normalize_url"]

from typing import List, Tuple
from playwright.async_api import (
    Page,
    TimeoutError as PlaywrightTimeout,
    Error as PlaywrightError,
)
import asyncio

from backend.config import (
    MAX_INTERACTION_DEPTH as MAX_DEPTH,
    NETWORK_IDLE_TIMEOUT as INTERACTION_TIMEOUT,
    INTERACTIVE_SELECTORS,
    MAX_TABS_TO_CLICK,
    MAX_TEXT_PREVIEW_LENGTH,
    TAB_CLICK_DELAY,
    LOAD_MORE_WAIT_TIME,
    SCROLL_WAIT_TIME,
    PAGINATION_WAIT_TIME,
)

# Extract selectors from config
TAB_SELECTORS = INTERACTIVE_SELECTORS["tabs"]
LOAD_MORE_SELECTORS = INTERACTIVE_SELECTORS["load_more"]
PAGINATION_SELECTORS = INTERACTIVE_SELECTORS["pagination"]


async def try_click_tabs(page: Page) -> List[str]:
    """Clicks up to MAX_TABS_TO_CLICK tabs to reveal hidden content."""
    clicks = []

    # Try to find tab containers
    for selector in TAB_SELECTORS:
        try:
            tabs = await page.query_selector_all(selector)

            if not tabs:
                continue

            # Click each tab (up to configured maximum)
            for i, tab in enumerate(tabs[:MAX_TABS_TO_CLICK]):
                try:
                    text = (await tab.inner_text()).strip()[:MAX_TEXT_PREVIEW_LENGTH]
                    await tab.click(timeout=INTERACTION_TIMEOUT)
                    clicks.append(f"Tab clicked: {selector} - {text}")
                    await asyncio.sleep(TAB_CLICK_DELAY)

                except (PlaywrightTimeout, PlaywrightError):
                    continue

            # If we found and clicked tabs, no need to try other selectors
            if clicks:
                break

        except (PlaywrightTimeout, PlaywrightError):
            continue

    return clicks


async def try_click_load_more(
    page: Page, max_clicks: int = MAX_DEPTH
) -> Tuple[List[str], int]:
    """Clicks "Load more"/"Show more" buttons up to max_clicks times."""
    clicks = []
    click_count = 0

    for attempt in range(max_clicks):
        clicked = False

        # Try each selector
        for selector in LOAD_MORE_SELECTORS:
            try:
                button = await page.query_selector(selector)
                if not button or not await button.is_visible():
                    continue

                text = (await button.inner_text()).strip()[:MAX_TEXT_PREVIEW_LENGTH]
                # Store element count instead of full HTML for efficiency
                element_count_before = await page.evaluate("() => document.querySelectorAll('*').length")
                
                await button.click(timeout=INTERACTION_TIMEOUT)
                clicks.append(f"Load more clicked ({attempt + 1}): {text}")
                click_count += 1
                clicked = True
                
                await asyncio.sleep(LOAD_MORE_WAIT_TIME)
                
                # Check if new elements were added
                element_count_after = await page.evaluate("() => document.querySelectorAll('*').length")
                if element_count_after <= element_count_before:
                    return clicks, click_count
                break

            except (PlaywrightTimeout, PlaywrightError):
                continue

        # If no button was clicked this round, we're done
        if not clicked:
            break

    return clicks, click_count


async def try_infinite_scroll(
    page: Page, max_scrolls: int = MAX_DEPTH
) -> Tuple[int, List[str]]:
    """Scrolls to bottom up to max_scrolls times, waiting for new content."""
    scroll_count = 0
    previous_height = 0
    visited_urls = []

    for attempt in range(max_scrolls):
        try:
            # Get current scroll height
            current_height = await page.evaluate("() => document.body.scrollHeight")

            # If height hasn't changed from last scroll, no new content
            if previous_height > 0 and current_height <= previous_height:
                break

            previous_height = current_height

            # Scroll to bottom
            await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")

            # Also try pressing End key to trigger some infinite scrolls that rely on keyboard events
            try:
                await page.keyboard.press("End")
            except Exception:
                pass

            scroll_count += 1

            # Wait for new content to load
            await asyncio.sleep(SCROLL_WAIT_TIME)

            # Optional: Wait for network to be idle
            try:
                await page.wait_for_load_state(
                    "networkidle", timeout=INTERACTION_TIMEOUT
                )
            except PlaywrightTimeout:
                pass

            # Check if URL changed (some infinite scrolls update URL)
            current_url = page.url
            if current_url not in visited_urls:
                visited_urls.append(current_url)

        except (PlaywrightTimeout, PlaywrightError, Exception):
            break

    return scroll_count, visited_urls


async def try_pagination(
    page: Page, max_pages: int = MAX_DEPTH
) -> Tuple[List[str], int, List[str]]:
    """Follows Next/pagination links up to max_pages, capturing HTML from each page."""
    pages_visited = [page.url]
    pages_count = 1
    html_contents = []

    # Capture initial page content
    try:
        content = await page.content()
        html_contents.append(content)
    except Exception:
        pass

    for attempt in range(max_pages - 1):  # -1 because we're already on page 1
        clicked = False

        # Try each pagination selector
        for selector in PAGINATION_SELECTORS:
            try:
                next_button = await page.query_selector(selector)
                if not next_button or not await next_button.is_visible():
                    continue

                url_before = page.url
                await next_button.click(timeout=INTERACTION_TIMEOUT)
                
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=INTERACTION_TIMEOUT)
                except PlaywrightTimeout:
                    await asyncio.sleep(1)

                url_after = page.url
                if url_after != url_before and url_after not in pages_visited:
                    pages_visited.append(url_after)
                    pages_count += 1
                    clicked = True
                    await asyncio.sleep(PAGINATION_WAIT_TIME)
                    html_contents.append(await page.content())
                    break

            except (PlaywrightTimeout, PlaywrightError):
                continue

        # If no pagination link worked, we're done
        if not clicked:
            break

    return pages_visited, pages_count, html_contents


async def handle_interactions(page: Page, strategy: str = "auto") -> dict:
    """
    Orchestrates depth ≥ 3 interactions: tabs, load more, scroll, pagination.
    Returns dict with clicks, scrolls, pages, and html_contents.
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
            scroll_count, scroll_pages = await try_infinite_scroll(
                page, max_scrolls=MAX_DEPTH
            )
            scrolls = scroll_count

            # Add new pages
            for p in scroll_pages:
                if p not in pages:
                    pages.append(p)

        if strategy in ["auto", "pagination", "all"]:
            # Try pagination (this changes the URL)
            pagination_pages, _, pagination_htmls = await try_pagination(
                page, max_pages=MAX_DEPTH
            )
            # Add new pages (avoid duplicates)
            for p in pagination_pages:
                if p not in pages:
                    pages.append(p)

            # Add HTML contents
            html_contents.extend(pagination_htmls)

        # For 'auto' strategy, if nothing worked, try remaining strategies as fallback
        if strategy == "auto" and not clicks and scrolls == 0 and len(pages) == 1:
            # Already tried tabs and load_more above, now try scroll and pagination
            scroll_count, scroll_pages = await try_infinite_scroll(
                page, max_scrolls=MAX_DEPTH
            )
            scrolls = scroll_count
            for p in scroll_pages:
                if p not in pages:
                    pages.append(p)

            # If scroll didn't work, try pagination
            if scrolls == 0:
                pagination_pages, _, pagination_htmls = await try_pagination(
                    page, max_pages=MAX_DEPTH
                )
                for p in pagination_pages:
                    if p not in pages:
                        pages.append(p)
                html_contents.extend(pagination_htmls)

    except Exception:
        # Don't fail completely on interaction errors
        pass

    return {
        "clicks": clicks,
        "scrolls": scrolls,
        "pages": pages,
        "html_contents": html_contents,
    }


def normalize_url(url: str) -> str:
    """Removes trailing slash for URL comparison."""
    return url.rstrip("/")
