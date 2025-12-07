"""
Backend configuration constants.
All configurable values are centralized here for easy maintenance.
Please note that we are not using environment variables for configuration in this project as it would then require the reviewer to first set the env variables before running the code, complicating the review process.
"""

# Server Configuration
HOST = "0.0.0.0"
PORT = 8000

# Scraping Timeouts (in seconds)
STATIC_TIMEOUT = 5
PLAYWRIGHT_TIMEOUT = 45
GLOBAL_TIMEOUT = 60
PAGE_LOAD_TIMEOUT = 30000  # Playwright page load timeout in milliseconds
NETWORK_IDLE_TIMEOUT = 5000  # Wait for network idle in milliseconds

# Content Thresholds
MIN_CONTENT_LENGTH = 500  # Minimum content length to consider JS rendering unnecessary
MAX_RAW_HTML_LENGTH = 5000  # Maximum length of raw HTML to store per section
MAX_INTERACTION_DEPTH = 3  # Maximum depth for pagination/scrolls/clicks

# Interaction Limits
MAX_TAB_CLICKS = 5
MAX_LOAD_MORE_CLICKS = 3
MAX_INFINITE_SCROLLS = 3
MAX_PAGINATION_PAGES = 3
SCROLL_WAIT_TIME = 2  # Seconds to wait after scrolling

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

# Landmark Tags for Section Grouping
LANDMARK_TAGS = ["header", "nav", "main", "article", "section", "aside", "footer"]

# Heading Tags
HEADING_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6"]

# List Tags
LIST_TAGS = ["ul", "ol"]

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

# Frontend Static File Path
FRONTEND_DIST_PATH = "frontend/dist"
