"""
Interaction handling - clicks, scrolls, and pagination for depth >= 3
"""
import asyncio
from typing import List, Tuple

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout, Error as PlaywrightError

from backend.config import (
    MAX_INTERACTION_DEPTH as MAX_DEPTH,
    NETWORK_IDLE_TIMEOUT as INTERACTION_TIMEOUT,
    INTERACTIVE_SELECTORS
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
            
            if not tabs:
                continue
            
            # Click each tab (up to MAX_DEPTH)
            for i, tab in enumerate(tabs[:MAX_DEPTH]):
                try:
                    # Check if tab is visible and enabled
                    is_visible = await tab.is_visible()
                    is_enabled = await tab.is_enabled()
                    
                    if not is_visible or not is_enabled:
                        continue
                    
                    # Get tab text for description
                    text = await tab.inner_text()
                    text = text.strip()[:50]  # Truncate
                    
                    # Click the tab
                    await tab.click(timeout=INTERACTION_TIMEOUT)
                    clicks.append(f"Tab clicked: {selector} - {text}")
                    
                    # Wait for content to load
                    await asyncio.sleep(0.5)
                    
                except (PlaywrightTimeout, PlaywrightError):
                    continue
            
            # If we found and clicked tabs, no need to try other selectors
            if clicks:
                break
                
        except (PlaywrightTimeout, PlaywrightError):
            continue
    
    return clicks


async def try_click_load_more(page: Page, max_clicks: int = MAX_DEPTH) -> Tuple[List[str], int]:
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
        
        # Try each selector
        for selector in LOAD_MORE_SELECTORS:
            try:
                # Check if button exists and is visible
                button = await page.query_selector(selector)
                
                if not button:
                    continue
                
                is_visible = await button.is_visible()
                if not is_visible:
                    continue
                
                # Get button text
                text = await button.inner_text()
                text = text.strip()[:50]
                
                # Get current content length (to detect if new content loaded)
                content_before = await page.content()
                len_before = len(content_before)
                
                # Click the button
                await button.click(timeout=INTERACTION_TIMEOUT)
                clicks.append(f"Load more clicked ({attempt + 1}): {text}")
                click_count += 1
                clicked = True
                
                # Wait for new content to load
                await asyncio.sleep(2)
                
                # Check if content actually changed
                content_after = await page.content()
                len_after = len(content_after)
                
                if len_after <= len_before:
                    # No new content, stop trying
                    return clicks, click_count
                
                break  # Successfully clicked, go to next attempt
                
            except (PlaywrightTimeout, PlaywrightError):
                continue
        
        # If no button was clicked this round, we're done
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
    previous_height = 0
    
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
            scroll_count += 1
            
            # Wait for new content to load
            await asyncio.sleep(2)
            
            # Optional: Wait for network to be idle
            try:
                await page.wait_for_load_state('networkidle', timeout=INTERACTION_TIMEOUT)
            except PlaywrightTimeout:
                pass
            
        except (PlaywrightTimeout, PlaywrightError, Exception):
            break
    
    return scroll_count


async def try_pagination(page: Page, max_pages: int = MAX_DEPTH) -> Tuple[List[str], int]:
    """
    Follow pagination links up to max_pages.
    
    Args:
        page: Playwright page
        max_pages: Maximum number of pages to visit (including current)
    
    Returns:
        (pages_visited, pages_count)
    """
    pages_visited = [page.url]
    pages_count = 1
    
    for attempt in range(max_pages - 1):  # -1 because we're already on page 1
        clicked = False
        
        # Try each pagination selector
        for selector in PAGINATION_SELECTORS:
            try:
                # Find next button/link
                next_button = await page.query_selector(selector)
                
                if not next_button:
                    continue
                
                is_visible = await next_button.is_visible()
                if not is_visible:
                    continue
                
                # Get current URL to detect if it changes
                url_before = page.url
                
                # Click next
                await next_button.click(timeout=INTERACTION_TIMEOUT)
                
                # Wait for navigation
                try:
                    await page.wait_for_load_state('domcontentloaded', timeout=INTERACTION_TIMEOUT)
                except PlaywrightTimeout:
                    await asyncio.sleep(1)  # Give it a moment anyway
                
                # Check if URL changed
                url_after = page.url
                
                if url_after != url_before and url_after not in pages_visited:
                    pages_visited.append(url_after)
                    pages_count += 1
                    clicked = True
                    
                    # Wait a bit for content to load
                    await asyncio.sleep(1)
                    
                    break  # Successfully navigated, try next page
                
            except (PlaywrightTimeout, PlaywrightError):
                continue
        
        # If no pagination link worked, we're done
        if not clicked:
            break
    
    return pages_visited, pages_count


async def handle_interactions(page: Page, strategy: str = 'auto') -> dict:
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
    """
    clicks = []
    scrolls = 0
    pages = [page.url]
    
    try:
        if strategy in ['auto', 'tabs', 'all']:
            # Try clicking tabs first
            tab_clicks = await try_click_tabs(page)
            clicks.extend(tab_clicks)
        
        if strategy in ['auto', 'load_more', 'all']:
            # Try "load more" buttons
            load_more_clicks, _ = await try_click_load_more(page, max_clicks=MAX_DEPTH)
            clicks.extend(load_more_clicks)
        
        if strategy in ['auto', 'scroll', 'all']:
            # Try infinite scroll
            scroll_count = await try_infinite_scroll(page, max_scrolls=MAX_DEPTH)
            scrolls = scroll_count
        
        if strategy in ['auto', 'pagination', 'all']:
            # Try pagination (this changes the URL)
            pagination_pages, _ = await try_pagination(page, max_pages=MAX_DEPTH)
            # Add new pages (avoid duplicates)
            for p in pagination_pages:
                if p not in pages:
                    pages.append(p)
        
        # For 'auto' strategy, if nothing worked, try everything
        if strategy == 'auto' and not clicks and scrolls == 0 and len(pages) == 1:
            # Try everything as fallback
            load_more_clicks, _ = await try_click_load_more(page, max_clicks=MAX_DEPTH)
            clicks.extend(load_more_clicks)
            
            scroll_count = await try_infinite_scroll(page, max_scrolls=MAX_DEPTH)
            scrolls = max(scrolls, scroll_count)
    
    except Exception:
        # Don't fail completely on interaction errors
        pass
    
    return {
        'clicks': clicks,
        'scrolls': scrolls,
        'pages': pages
    }
