"""
Main scraping orchestrator - coordinates static and dynamic scraping with fallback
"""

from datetime import datetime, timezone

from backend.models import ScrapeResult, ScrapeError, Meta, Interactions
from backend.scraper.dynamic import scrape_dynamic
from backend.scraper.static import scrape_static
from backend.scraper.utils import validate_url, check_robots_txt


def _error_result(url: str, errors: list[ScrapeError]) -> ScrapeResult:
    """Create an error result with minimal structure."""
    return ScrapeResult(
        url=url,
        scrapedAt=datetime.now(timezone.utc).isoformat(),
        meta=Meta(title="Error", description="", language="en", canonical=None),
        sections=[],
        interactions=Interactions(),
        errors=errors,
    )


async def scrape_url(
    url: str, enable_interactions: bool = False, interaction_strategy: str = "auto"
) -> ScrapeResult:
    """
    Scrapes a URL with intelligent static→dynamic fallback.
    Always returns a result (errors logged in result.errors).

    Args:
        url: Target URL
        enable_interactions: Enable depth ≥ 3 interactions (tabs, pagination, etc.)
        interaction_strategy: 'auto', 'tabs', 'load_more', 'scroll', 'pagination', or 'all'
    """
    # Validate URL
    is_valid, error_msg = validate_url(url)
    if not is_valid:
        return _error_result(url, [ScrapeError(message=error_msg, phase="validation")])

    # Check robots.txt compliance
    is_allowed, robots_msg = await check_robots_txt(url)
    if not is_allowed:
        return _error_result(url, [ScrapeError(message=robots_msg, phase="validation")])

    errors = []

    try:
        # If interactions enabled, skip static and go directly to Playwright
        if enable_interactions:
            dynamic_result = await scrape_dynamic(
                url, enable_interactions=True, interaction_strategy=interaction_strategy
            )
            return dynamic_result or _error_result(url, errors)
        
        # Try static scraping first
        static_result, needs_js = await scrape_static(url)

        if static_result and not needs_js:
            return static_result

        # Fallback to dynamic with auto-enabled interactions
        errors.append(
            ScrapeError(
                message="Static HTML insufficient - using JavaScript rendering with interactions",
                phase="fallback",
            )
        )
        dynamic_result = await scrape_dynamic(
            url, enable_interactions=needs_js, interaction_strategy=interaction_strategy
        )
        
        result = dynamic_result or static_result
        if result:
            result.errors.extend(errors)
            return result

    except Exception as e:
        errors.append(
            ScrapeError(
                message=f"Unexpected error during scraping: {str(e)}",
                phase="orchestration",
            )
        )

    return _error_result(url, errors)
