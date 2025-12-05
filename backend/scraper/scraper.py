"""
Main scraping orchestrator - coordinates static and dynamic scraping with fallback
"""
from datetime import datetime

from backend.models import ScrapeResult, ScrapeError, Meta, Interactions
from backend.scraper.static import scrape_static
from backend.scraper.dynamic import scrape_dynamic
from backend.scraper.utils import validate_url


async def scrape_url(
    url: str, 
    enable_interactions: bool = False,
    interaction_strategy: str = 'auto'
) -> ScrapeResult:
    """
    Main scraping function with fallback strategy.
    
    Strategy:
    1. Validate URL
    2. Attempt static scraping (fast)
    3. Check if JS rendering is needed (heuristic)
    4. If needed, fallback to Playwright (slower)
    5. Optionally handle interactions (clicks, scrolls, pagination)
    6. Return best available result
    
    Args:
        url: URL to scrape
        enable_interactions: Whether to handle interactions (depth >= 3)
        interaction_strategy: Strategy for interactions ('auto', 'tabs', 'load_more', 'scroll', 'pagination', 'all')
    
    This always returns a ScrapeResult (may contain errors).
    """
    errors = []
    
    # Validate URL first
    is_valid, error_msg = validate_url(url)
    if not is_valid:
        # Return error result immediately
        return ScrapeResult(
            url=url,
            scrapedAt=datetime.utcnow().isoformat() + "Z",
            meta=Meta(title="Error", description="", language="en", canonical=None),
            sections=[],
            interactions=Interactions(),
            errors=[ScrapeError(message=error_msg, phase="validation")]
        )
    
    try:
        # Step 1: Try static scraping first
        static_result, needs_js = await scrape_static(url)
        
        if static_result and not needs_js:
            # Static scraping succeeded and content is sufficient
            return static_result
        
        # Step 2: Static failed or needs JS - use Playwright
        if needs_js or static_result is None:
            # Add info about fallback
            if needs_js:
                errors.append(ScrapeError(
                    message="Static HTML insufficient - using JavaScript rendering",
                    phase="fallback"
                ))
            
            dynamic_result = await scrape_dynamic(
                url, 
                enable_interactions=enable_interactions,
                interaction_strategy=interaction_strategy
            )
            
            if dynamic_result:
                # Merge any errors from static attempt
                dynamic_result.errors.extend(errors)
                return dynamic_result
            
            # Both failed - return whatever we have
            if static_result:
                errors.append(ScrapeError(
                    message="Dynamic scraping failed - returning static result",
                    phase="fallback"
                ))
                static_result.errors.extend(errors)
                return static_result
            
            # Complete failure
            errors.append(ScrapeError(
                message="Both static and dynamic scraping failed",
                phase="scraping"
            ))
    
    except Exception as e:
        errors.append(ScrapeError(
            message=f"Unexpected error during scraping: {str(e)}",
            phase="orchestration"
        ))
    
    # Return error result
    return ScrapeResult(
        url=url,
        scrapedAt=datetime.utcnow().isoformat() + "Z",
        meta=Meta(title="Error", description="", language="en", canonical=None),
        sections=[],
        interactions=Interactions(pages=[url]),
        errors=errors
    )
