"""Validation, robots.txt checks, and JS detection heuristics."""

__all__ = ["check_robots_txt", "validate_url", "needs_js_rendering"]

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
    MAX_SCRIPT_COUNT_THRESHOLD,
)


async def check_robots_txt(url: str, user_agent: str = "*") -> Tuple[bool, str]:
    """Checks robots.txt compliance. Returns (is_allowed, message)."""
    # Validate user_agent parameter
    if not user_agent or not user_agent.strip():
        user_agent = "*"
    
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
                    return (
                        True,
                        f"Could not fetch robots.txt (status {response.status_code}) - proceeding anyway",
                    )

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
    """Validates URL: http(s) scheme, well-formed, max 2048 chars."""
    if not url or not url.strip():
        return False, "URL is required"

    url = url.strip()
    
    # Security: Prevent extremely long URLs (DoS risk)
    if len(url) > 2048:
        return False, "URL exceeds maximum length of 2048 characters"
    
    if not url.startswith(("http://", "https://")):
        return False, "Only http:// and https:// URLs are supported"

    try:
        parsed = urlparse(url)
        return (True, "") if parsed.netloc else (False, "Invalid URL format")
    except Exception as e:
        return False, f"Invalid URL: {str(e)}"


def needs_js_rendering(html: str) -> bool:
    """Heuristic detection: SPA markers, low content, high script count."""
    """
    Heuristic to determine if page needs JavaScript rendering.

    Triggers JS rendering if:
    - SPA/CSR framework markers detected (React, Next.js, Vue, etc.)
    - Content length < 500 chars
    - No <main> or <article> tags
    - Contains "enable JavaScript" messages
    - High script-to-content ratio
    - Heavy bundled scripts with low text ratio

    Returns True if Playwright should be used.
    """
    soup = BeautifulSoup(html, "lxml")

    # 1) Check for SPA/CSR framework markers
    # React/Next.js/Gatsby
    if soup.find(id="__next") or soup.find(id="___gatsby"):
        return True
    if soup.find(attrs={"data-reactroot": True}) or soup.find(
        attrs={"data-react-helmet": True}
    ):
        return True
    # Generic SPA roots
    if soup.find(id="root") or soup.find(id="app") or soup.find(class_="react-root"):
        return True
    # Vue.js
    if soup.find(id="app", attrs={"data-v-app": True}):
        return True

    # 2) Check for JS required messages (from noscript or main text)
    noscripts = " ".join(
        ns.get_text(" ", strip=True).lower() for ns in soup.find_all("noscript")
    )
    if (
        "enable javascript" in noscripts
        or "without javascript" in noscripts
        or "javascript is required" in noscripts
    ):
        return True

    text = soup.get_text().lower()
    if any(phrase in text for phrase in JS_REQUIRED_PHRASES):
        return True

    # 3) Analyze script tags before removing them
    scripts = soup.find_all("script")
    script_count = len(scripts)

    # Check for bundled script patterns (webpack, next, vite, etc.)
    bundler_keywords = (
        "bundle",
        "chunk",
        "webpack",
        "main.",
        "next",
        "app.",
        "vendor",
        "_next",
        "vite",
    )
    # Use generator to avoid building intermediate list
    has_heavy_bundles = any(
        any(k in s.get("src", "").lower() for k in bundler_keywords)
        for s in scripts
        if s.get("src")
    )

    # 4) Remove script and style tags for content analysis
    for tag in soup.find_all(["script", "style", "noscript"]):
        tag.decompose()

    # 5) Compute text-to-HTML ratio
    clean_text = soup.get_text(separator=" ", strip=True)
    clean_text = re.sub(r"\s+", " ", clean_text)
    content_length = len(clean_text)
    html_len = max(len(html), 1)
    text_ratio = content_length / html_len

    # 6) Too little content
    if content_length < MIN_CONTENT_LENGTH:
        return True

    # 7) No semantic markers
    if not (
        soup.find("main") or soup.find("article") or soup.find(attrs={"role": "main"})
    ):
        return True

    # 8) Heavy JS with low text ratio (likely CSR shell)
    if has_heavy_bundles and script_count > 10 and text_ratio < 0.03:
        return True

    # 9) Very high script count with low text ratio
    if script_count > 30 and text_ratio < 0.05:
        return True

    # 10) Original script-to-content ratio check
    if (
        script_count > MAX_SCRIPT_COUNT_THRESHOLD
        and content_length < MIN_SEMANTIC_CONTENT_LENGTH
    ):
        return True

    return False
