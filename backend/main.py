"""
FastAPI application for web scraping service.

This module provides the main API endpoints for scraping websites
with intelligent static/dynamic fallback and interaction handling.
"""
from pathlib import Path
import mimetypes

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import Field

from backend.models import ScrapeRequest, ScrapeResult
from backend.config import HOST, PORT, FRONTEND_DIST_PATH

# Fix MIME type for JavaScript files
mimetypes.add_type('application/javascript', '.js')


class ScrapeRequestExtended(ScrapeRequest):
    """
    Extended scrape request with interaction options.
    
    Attributes:
        url: Target URL to scrape (inherited from ScrapeRequest)
        enableInteractions: Whether to handle user interactions
        interactionStrategy: Strategy for handling interactions
    """
    enable_interactions: bool = Field(
        default=False,
        description="Enable interaction handling (clicks, scrolls, pagination)"
    )
    interaction_strategy: str = Field(
        default='auto',
        description="Interaction strategy: 'auto', 'tabs', 'load_more', 'scroll', 'pagination', 'all'"
    )


app = FastAPI(
    title="LyftrAI Assignment",
    description="Advanced web scraping API with static and dynamic rendering support",
    version="1.0.0"
)

# CORS middleware (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.post("/scrape", response_model=ScrapeResult)
async def scrape_url_endpoint(request: ScrapeRequestExtended):
    """
    Main scraping endpoint - accepts URL and returns structured data.
    
    Uses intelligent fallback strategy:
    1. Try static scraping first (fast)
    2. If content insufficient, use Playwright (JS rendering)
    3. Optionally handle interactions (clicks, scrolls, pagination) for depth >= 3
    4. Always returns a result (may contain errors)
    
    Args:
        request: ScrapeRequestExtended with URL and interaction options
        
    Returns:
        ScrapeResult: Structured scraping result with sections and metadata
        
    Raises:
        HTTPException: If URL scheme is invalid
    """
    from backend.scraper import scrape_url
    
    # Validate URL scheme
    if not request.url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400,
            detail="Only http:// and https:// URLs are supported"
        )
    
    # Perform scraping with fallback
    result = await scrape_url(
        request.url,
        enable_interactions=request.enable_interactions,
        interaction_strategy=request.interaction_strategy
    )
    
    return result


# Serve React frontend static files
frontend_dist = Path(__file__).parent.parent / FRONTEND_DIST_PATH

if frontend_dist.exists():
    # Mount static assets directory
    app.mount(
        "/assets", 
        StaticFiles(directory=str(frontend_dist / "assets")), 
        name="assets"
    )
    
    # Serve vite.svg at root
    @app.get("/vite.svg")
    async def serve_vite_svg():
        """Serve vite.svg from root"""
        return FileResponse(frontend_dist / "vite.svg", media_type="image/svg+xml")
    
    @app.get("/")
    async def serve_index():
        """Serve index.html at root"""
        return FileResponse(frontend_dist / "index.html", media_type="text/html")
else:
    @app.get("/")
    async def root():
        """Fallback response when frontend is not built yet."""
        return {
            "message": "Lyftr AI Web Scraper API",
            "status": "Frontend not built yet. Run: cd frontend && npm install && npm run build",
            "endpoints": {
                "health": "GET /healthz",
                "scrape": "POST /scrape"
            }
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
