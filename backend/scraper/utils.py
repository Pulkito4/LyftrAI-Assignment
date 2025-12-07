"""
Utility functions for scraping operations
"""
import re
import httpx
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from typing import Tuple


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
        async with httpx.AsyncClient(timeout=5.0) as client:
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


def get_content_length(html: str) -> int:
    """
    Get approximate text content length from HTML.
    Used for heuristic to determine if JS rendering is needed.
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Remove script and style tags
    for tag in soup.find_all(['script', 'style', 'noscript']):
        tag.decompose()
    
    text = soup.get_text(separator=' ', strip=True)
    # Clean whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return len(text)


def has_main_content_marker(html: str) -> bool:
    """
    Check if HTML has semantic content markers like <main> or <article>.
    Used in heuristic for JS rendering decision.
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Check for main content tags
    if soup.find('main') or soup.find('article'):
        return True
    
    # Check for role="main"
    if soup.find(attrs={'role': 'main'}):
        return True
    
    return False


# Phrases that indicate JavaScript is required
JS_REQUIRED_PHRASES = [
    'enable javascript',
    'please enable javascript',
    'javascript is required',
    'javascript is disabled',
    'requires javascript',
    'loading...',
    'just a moment',
    'checking your browser',
    'please wait',
    'redirecting...',
]


def has_js_required_message(html: str) -> bool:
    """
    Check if page contains messages indicating JavaScript is required.
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, 'lxml')
    text = soup.get_text().lower()
    
    return any(phrase in text for phrase in JS_REQUIRED_PHRASES)


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
    # Check for JS required messages first
    if has_js_required_message(html):
        return True
    
    # Get content length
    content_length = get_content_length(html)
    
    # Too little content
    if content_length < 500:
        return True
    
    # No semantic markers
    if not has_main_content_marker(html):
        return True
    
    # Check script-to-content ratio
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'lxml')
    script_count = len(soup.find_all('script'))
    
    if script_count > 20 and content_length < 2000:
        return True
    
    return False
