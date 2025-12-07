"""
Backend configuration constants.
All configurable values are centralized here for easy maintenance.
Please note that we are not using environment variables for configuration in this project as it would then require the reviewer to first set the env variables before running the code, complicating the review process.
"""

# Server Configuration
HOST = "0.0.0.0"
PORT = 8000

# Scraping Timeouts (in seconds)
STATIC_TIMEOUT = 10.0  # HTTP client timeout for static scraping
ROBOTS_TXT_TIMEOUT = 5.0  # Timeout for fetching robots.txt
PAGE_LOAD_TIMEOUT = 30000  # Playwright page load timeout in milliseconds
NETWORK_IDLE_TIMEOUT = 5000  # Wait for network idle in milliseconds
SELECTOR_WAIT_TIMEOUT = 2000  # Wait for specific selectors in milliseconds

# Content Thresholds
MIN_CONTENT_LENGTH = 500  # Minimum content length to consider JS rendering unnecessary
MIN_SEMANTIC_CONTENT_LENGTH = 2000  # Minimum content for high script count tolerance
MAX_SCRIPT_COUNT_THRESHOLD = 20  # Maximum scripts before requiring more content
MAX_RAW_HTML_LENGTH = 5000  # Maximum length of raw HTML to store per section
MAX_INTERACTION_DEPTH = 3  # Maximum depth for pagination/scrolls/clicks
MAX_URL_LENGTH = 2048  # Maximum allowed URL length (security)

# Interaction Configuration
MAX_TABS_TO_CLICK = 5  # Maximum number of tabs to click
MAX_TEXT_PREVIEW_LENGTH = 50  # Maximum length of text preview in interaction logs
TAB_CLICK_DELAY = 0.5  # Delay in seconds between tab clicks
LOAD_MORE_WAIT_TIME = 2  # Wait time in seconds after clicking load more
SCROLL_WAIT_TIME = 2  # Wait time in seconds after scroll
PAGINATION_WAIT_TIME = 1  # Wait time in seconds after pagination

# Browser Configuration
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080

# Main Content Selectors for Dynamic Waiting
MAIN_CONTENT_SELECTORS = ["main", "article", '[role="main"]', "#content", ".content"]

# HTTP Headers
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

# Noise Removal Selectors
NOISE_SELECTORS = [
    "script",
    "style",
    "noscript",
    "[role='dialog']",
    "[class*='cookie']",
    "[class*='gdpr']",
    "[id*='cookie']",
    "[class*='popup']",
    "[class*='modal']",
    "[class*='overlay']",
    "[class*='banner']",
    ".advertisement",
    ".ad-container",
    "[class*='consent']",
]

# JS Detection Phrases
JS_REQUIRED_PHRASES = [
    "javascript is required",
    "enable javascript",
    "javascript disabled",
    "please enable javascript",
    "requires javascript",
    "javascript is not enabled",
]

# Interactive Elements for Interaction Detection
INTERACTIVE_SELECTORS = {
    "tabs": [
        "[role='tab']",
        ".tab",
        "[class*='tab']",
        "button[aria-selected]",
    ],
    "load_more": [
        "button:has-text('Load more')",
        "button:has-text('Show more')",
        "a:has-text('Load more')",
        "[class*='load-more']",
        "[class*='show-more']",
    ],
    "pagination": [
        "a:has-text('Next')",
        "button:has-text('Next')",
        "[rel='next']",
        "[class*='next']",
        "[class*='pagination'] a",
    ],
}

# Section Type Classification Keywords
SECTION_TYPE_KEYWORDS = {
    "hero": ["hero", "banner", "jumbotron", "splash"],
    "nav": ["nav", "navigation", "menu"],
    "footer": ["footer", "copyright"],
    "pricing": ["pricing", "price", "plan"],
    "faq": ["faq", "question", "answer", "accordion"],
    "list": ["list", "items"],
    "grid": ["grid", "gallery", "cards"],
}

# Frontend Static File Path
FRONTEND_DIST_PATH = "frontend/dist"
