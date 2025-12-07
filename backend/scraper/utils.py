"""
Utility functions for scraping operations
"""
import re
from typing import Tuple
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from backend.config import (
    JS_REQUIRED_PHRASES, 
    MIN_CONTENT_LENGTH, 
    ROBOTS_TXT_TIMEOUT,
    MIN_SEMANTIC_CONTENT_LENGTH,
    MAX_SCRIPT_COUNT_THRESHOLD
)


async def check_robots_txt(url: str, user_agent: str = "*") -> Tuple[bool, str]:
    """
    Check if URL is allowed by robots.txt.
    
    Args:
        url: URL to check
        user_agent: User agent to check for (default: *)
    
    Returns:
        (is_allowed, message)
    """
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        # Fetch robots.txt with timeout
        async with httpx.AsyncClient(timeout=ROBOTS_TXT_TIMEOUT) as client:
            try:
                response = await client.get(robots_url)
                if response.status_code == 404:
                    # No robots.txt means all allowed
                    return True, "No robots.txt found - scraping allowed"
                
                if response.status_code != 200:
                    # Other errors - allow but warn
                    return True, f"Could not fetch robots.txt (status {response.status_code}) - proceeding anyway"
                
                # Parse robots.txt
                rp = RobotFileParser()
                rp.parse(response.text.splitlines())
                
                # Check if our path is allowed
                is_allowed = rp.can_fetch(user_agent, url)
                
                if not is_allowed:
                    return False, "URL disallowed by robots.txt"
                
                return True, "Robots.txt allows scraping"
                
            except httpx.TimeoutException:
                return True, "Robots.txt fetch timeout - proceeding anyway"
            except Exception as e:
                return True, f"Error checking robots.txt: {str(e)} - proceeding anyway"
                
    except Exception as e:
        return True, f"Error parsing robots.txt URL: {str(e)} - proceeding anyway"


def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate that URL is http(s) and well-formed.
    Returns (is_valid, error_message)
    """
    if not url:
        return False, "URL is required"
    
    url = url.strip()
    
    # Check scheme
    if not url.startswith(('http://', 'https://')):
        return False, "Only http:// and https:// URLs are supported"
    
    # Parse URL
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return False, "Invalid URL format"
        return True, ""
    except Exception as e:
        return False, f"Invalid URL: {str(e)}"


def needs_js_rendering(html: str) -> bool:
    """
    Heuristic to determine if page needs JavaScript rendering.
    
    Triggers JS rendering if:
    - Content length < 500 chars
    - No <main> or <article> tags
    - Contains "enable JavaScript" messages
    - High script-to-content ratio
    
    Returns True if Playwright should be used.
    """
    soup = BeautifulSoup(html, 'lxml')
    
    # Check for JS required messages
    text = soup.get_text().lower()
    if any(phrase in text for phrase in JS_REQUIRED_PHRASES):
        return True
    
    # Remove script and style tags for content analysis
    for tag in soup.find_all(['script', 'style', 'noscript']):
        tag.decompose()
    
    # Get content length
    clean_text = soup.get_text(separator=' ', strip=True)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    content_length = len(clean_text)
    
    # Too little content
    if content_length < MIN_CONTENT_LENGTH:
        return True
    
    # No semantic markers
    if not (soup.find('main') or soup.find('article') or soup.find(attrs={'role': 'main'})):
        return True
    
    # Check script-to-content ratio
    script_count = len(soup.find_all('script'))
    if script_count > MAX_SCRIPT_COUNT_THRESHOLD and content_length < MIN_SEMANTIC_CONTENT_LENGTH:
        return True
    
    return False
