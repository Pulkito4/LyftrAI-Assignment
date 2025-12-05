# LyftrAI Assignment - Advanced Web Scraper

A full-stack web scraping application with static and dynamic rendering capabilities, interaction handling for depth ≥ 3, and a modern React UI.

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 22.x or higher
- Git

### Installation & Running

**Option 1: Using the automated script (Recommended)**

**Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

**Windows:**
```powershell
.\run.ps1
```

**Option 2: Manual setup**

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install backend dependencies
pip install -r requirements.txt

# 3. Install Playwright browsers
playwright install chromium

# 4. Install frontend dependencies and build
cd frontend
npm install
npm run build
cd ..

# 5. Start the server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

The application will be available at: **http://localhost:8000**

## 📋 Project Structure

```
LyfterAI/
├── backend/
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Configuration constants
│   ├── main.py                  # FastAPI application entry point
│   ├── models.py                # Pydantic data models
│   └── scraper/
│       ├── __init__.py          # Scraper package exports
│       ├── dynamic.py           # Playwright-based dynamic scraper
│       ├── interactions.py      # Interaction handlers (tabs, pagination, etc.)
│       ├── parser.py            # HTML parsing and section extraction
│       ├── scraper.py           # Main orchestrator with fallback logic
│       ├── static.py            # httpx-based static scraper
│       └── utils.py             # Validation and heuristic utilities
├── frontend/
│   ├── src/
│   │   ├── components/          # React components (shadcn/ui)
│   │   ├── constants.js         # Frontend configuration
│   │   ├── App.jsx              # Main application
│   │   └── index.css            # Tailwind CSS imports
│   ├── index.html               # HTML entry point
│   ├── jsconfig.json            # Path aliases configuration
│   ├── vite.config.js           # Vite build configuration
│   └── package.json             # Frontend dependencies
├── requirements.txt             # Python dependencies
├── run.sh                       # Linux/Mac setup script
├── run.ps1                      # Windows PowerShell setup script
├── README.md                    # This file
├── design_notes.md              # Architecture and design decisions
└── capabilities.json            # Feature flags and capabilities
```

## 🎯 Features

### Core Scraping Capabilities

- **Static Scraping** - Fast httpx-based requests with User-Agent headers
- **Dynamic Scraping** - Playwright with Chromium for JavaScript-heavy sites
- **Smart Fallback** - Automatic detection and fallback from static to dynamic
- **Heuristic Detection** - Content length, markers, and JS phrase analysis

### Interaction Handling (Depth ≥ 3)

- **Tabs** - Clicks up to 5 tab elements
- **Load More Buttons** - Clicks "Load more"/"Show more" buttons (max 3)
- **Infinite Scroll** - Scrolls to bottom with 2s delays (max 3)
- **Pagination** - Follows "Next" page links (max 3 pages)
- **Auto Mode** - Smart detection and execution of all strategies

### HTML Parsing & Structure

- **Semantic Sections** - Groups by HTML5 landmarks (`<header>`, `<main>`, `<nav>`, `<footer>`)
- **Heading Groups** - Falls back to h1-h3 heading hierarchy
- **Section Types** - Classifies as hero, nav, footer, pricing, FAQ, list, grid, or generic
- **Content Extraction** - Extracts headings, text, links, images, lists, and tables
- **Noise Filtering** - Removes cookie banners, modals, ads, scripts, and styles

### API & Frontend

- **FastAPI Backend** - RESTful API with `/scrape` and `/healthz` endpoints
- **React UI** - Modern interface with Tailwind CSS and shadcn/ui components
- **Real-time Feedback** - Loading states, error handling, and progress indicators
- **JSON Export** - Download scraped data as structured JSON
- **Tabbed Results** - View sections, raw JSON, or interaction details

## 🧪 Testing URLs

Three URLs were used for comprehensive testing:

### 1. example.com (Simple Static)
```json
{
  "url": "http://example.com",
  "enableInteractions": false,
  "interactionStrategy": "auto"
}
```
**Result:** 1 section extracted, 112 characters of content  
**Notes:** Minimal page, static scraping sufficient

### 2. Wikipedia - Web_scraping (Rich Static)
```json
{
  "url": "https://en.wikipedia.org/wiki/Web_scraping",
  "enableInteractions": false,
  "interactionStrategy": "auto"
}
```
**Result:** 5 sections, 1158+ characters  
**Notes:** Requires User-Agent header, rich semantic structure

### 3. Hacker News (Pagination - Depth 3)
```json
{
  "url": "https://news.ycombinator.com/",
  "enableInteractions": true,
  "interactionStrategy": "pagination"
}
```
**Result:** 3 pages visited, pagination depth requirement met  
**Notes:** Tests interaction handling with "More" link following

## 🏗️ Architecture Highlights

### Static → Dynamic Fallback Strategy

1. **Attempt Static** - Try httpx with 10s timeout
2. **Check Heuristic** - Evaluate content length, markers, JS requirements
3. **Fallback to Playwright** - Launch Chromium if needed
4. **Wait Strategy** - `domcontentloaded` → `networkidle` → selector waits → 1s buffer
5. **Execute Interactions** - Run depth ≥ 3 clicks/scrolls/pagination if enabled

### Timeout Management

- **Static Scraper:** 10 seconds
- **Playwright Scraper:** 45 seconds (with interaction buffer)
- **Global Timeout:** 60 seconds total
- **Buffer:** 10 seconds for processing

### Content Grouping Logic

1. **Try Landmarks** - Group by `<header>`, `<main>`, `<article>`, `<section>`, `<aside>`, `<nav>`, `<footer>`
2. **Fallback to Headings** - Use h1-h3 hierarchy if landmarks insufficient
3. **Label Generation** - Use first heading or first 5-7 words of content
4. **Type Classification** - Detect hero, nav, footer, pricing, FAQ patterns

## 🔧 Configuration

### Backend (`backend/config.py`)

```python
SCRAPING_TIMEOUT = 60.0          # Global timeout
STATIC_TIMEOUT = 10.0            # httpx timeout
DYNAMIC_TIMEOUT = 45.0           # Playwright timeout
MAX_INTERACTION_DEPTH = 3        # Clicks/scrolls/pages
USER_AGENT = "Mozilla/5.0..."    # Browser user agent
```

### Frontend (`frontend/src/constants.js`)

```javascript
API_ENDPOINTS = {
  SCRAPE: '/scrape',
  HEALTH: '/healthz'
}

INTERACTION_STRATEGIES = [
  'auto', 'tabs', 'load_more', 'scroll', 'pagination', 'all'
]

UI_CONFIG = {
  MAX_PREVIEW_LENGTH: 300,
  MAX_HEADINGS_DISPLAY: 5,
  // ...
}
```

## 📊 API Documentation

### POST /scrape

**Request:**
```json
{
  "url": "https://example.com",
  "enableInteractions": true,
  "interactionStrategy": "auto"
}
```

**Response:**
```json
{
  "url": "https://example.com",
  "timestamp": "2025-12-05T10:30:00Z",
  "meta": {
    "title": "Example Domain",
    "description": "Example description",
    "language": "en",
    "canonical": "https://example.com"
  },
  "sections": [
    {
      "id": "section-1",
      "type": "section",
      "label": "Example Domain",
      "content": {
        "headings": ["Example Domain"],
        "text": "This domain is for use in illustrative examples...",
        "links": [{"text": "More information...", "href": "..."}],
        "images": [],
        "lists": [],
        "tables": []
      },
      "rawHtml": "<div>...</div>",
      "truncated": false
    }
  ],
  "interactions": {
    "pages": ["https://example.com"],
    "clicks": [],
    "scrolls": 0
  },
  "errors": []
}
```

### GET /healthz

**Response:**
```json
{
  "status": "ok"
}
```

## 🛠️ Technology Stack

### Backend
- **FastAPI 0.104.1** - Modern async web framework
- **Pydantic 2.5.0** - Data validation and serialization
- **httpx 0.25.1** - Async HTTP client for static scraping
- **Playwright 1.40.0** - Browser automation for dynamic scraping
- **BeautifulSoup4 4.12.2** - HTML parsing
- **lxml 4.9.3** - Fast XML/HTML parser
- **uvicorn 0.24.0** - ASGI server

### Frontend
- **React 18** - UI library
- **Vite 7.2.6** - Build tool
- **Tailwind CSS v4** - Utility-first styling
- **shadcn/ui** - Component library
- **Node.js 22.20.0** - Runtime environment

## 📝 Known Limitations

1. **Infinite Scroll Detection** - Requires site-specific logic; may not work on all sites
2. **Content Truncation** - Raw HTML limited to 5000 characters per section
3. **Image Loading** - External images may not load if CORS restricted
4. **Rate Limiting** - No built-in rate limiting; may trigger anti-bot measures on some sites
5. **JavaScript Execution** - Some complex SPAs may require additional wait strategies

## 🔐 Security Considerations

- **URL Validation** - Only http/https protocols allowed
- **Timeout Protection** - Prevents long-running scrapes
- **Error Handling** - Graceful degradation with error reporting
- **CORS Headers** - Configured for frontend-backend communication

## 📄 License

This project is created for the LyftrAI assignment evaluation.

## 👤 Author

Built for LyftrAI Assignment Submission

---

**Last Updated:** December 5, 2025
