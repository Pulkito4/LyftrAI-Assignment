# LyftrAI Assignment - Advanced Web Scraper

A full-stack web scraping application with static/dynamic fallback, interaction handling for depth ≥ 3, and a modern React UI.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 22.x+
- Git

### Setup & Run

**Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

**Windows:**
```powershell
.\run.ps1
```

The application will be available at: **http://localhost:8000**

### Automation Note
The scripts automatically handle:
1. Virtual environment creation & dependency installation
2. Playwright browser binaries download (~300MB)
3. Frontend build (`npm run build`)
4. Server startup


---

## 🧪 Test URLs

Three URLs used for testing with specific characteristics:

### 1. **http://example.com** — Simple Static Page
- **Type:** Minimal HTML, no JavaScript
- **Result:** 1 section, ~112 characters
- **Tests:** Basic static scraping, fast response (<1s)

### 2. **https://en.wikipedia.org/wiki/Web_scraping** — Rich Static Content
- **Type:** Complex HTML with tables, lists, links
- **Result:** 5+ sections, 1000+ characters
- **Tests:** Semantic section grouping, User-Agent handling, noise filtering

### 3. **https://news.ycombinator.com/** — Pagination (Depth 3)
- **Type:** Server-side rendered with "More" pagination link
- **Result:** 3 pages visited, depth requirement met
- **Tests:** Interaction handling, pagination strategy, multiple page scraping
- **Config:** `{"enable_interactions": true, "interaction_strategy": "pagination"}`

---

## 📊 API Usage

### Interactive Docs
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Endpoint: POST /scrape

**Request Body:**
```json
{
  "url": "https://example.com",
  "enable_interactions": false,
  "interaction_strategy": "auto"
}
```

**Fields:**
- `url` (required) - Target URL to scrape
- `enable_interactions` (optional, default: false) - Enable depth ≥ 3 interactions
- `interaction_strategy` (optional, default: "auto") - Strategy: `"auto"`, `"tabs"`, `"load_more"`, `"scroll"`, `"pagination"`, `"all"`

**cURL Example:**
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://news.ycombinator.com/",
    "enable_interactions": true,
    "interaction_strategy": "pagination"
  }'
```

**PowerShell Example:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/scrape" -Method Post `
  -Body '{"url": "https://news.ycombinator.com/", "enable_interactions": true}' `
  -ContentType "application/json"
```

**Response Structure:**
```json
{
  "url": "https://example.com",
  "scrapedAt": "2025-12-07T10:30:00+00:00",
  "meta": {
    "title": "Page Title",
    "description": "Page description",
    "language": "en",
    "canonical": "https://example.com",
    "strategy": "static"
  },
  "sections": [
    {
      "id": "section-0",
      "type": "hero",
      "label": "Main Heading",
      "sourceUrl": "https://example.com",
      "content": {
        "headings": ["Example Domain"],
        "text": "This domain is for use...",
        "links": [{"text": "More info", "href": "..."}],
        "images": [],
        "lists": [],
        "tables": []
      },
      "rawHtml": "<div>...</div>",
      "truncated": false
    }
  ],
  "interactions": {
    "clicks": [],
    "scrolls": 0,
    "pages": ["https://example.com"]
  },
  "errors": []
}
```

---

## 📝 Known Limitations

1. **Anti-bot Protection** - Sites with aggressive bot detection may block requests
2. **Content Truncation** - Raw HTML limited to 5000 chars per section
3. **Infinite Scroll** - May not work on all implementations (site-specific)
4. **Rate Limiting** - No built-in rate limiting; use responsibly
5. **Complex SPAs** - Some React/Vue apps may need additional wait strategies

---

## 🛠️ Troubleshooting

### Playwright Errors
```bash
playwright install chromium
playwright install-deps  # Linux only
```

### Frontend Not Building
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Port 8000 Already in Use
```bash
# Kill process on port 8000
# Windows: netstat -ano | findstr :8000
# Linux/Mac: lsof -ti:8000 | xargs kill
```

---

## 🔧 Tech Stack

**Backend:** FastAPI, Pydantic, httpx, Playwright, BeautifulSoup4  
**Frontend:** React, Vite, Tailwind CSS v4, shadcn/ui  
**Runtime:** Python 3.11+, Node.js 22.x+

---

## 📖 Documentation

- **design_notes.md** - Implementation strategy and decisions
- **ARCHITECTURE.md** - Key design decisions (Monolith, Pydantic, Async, EAFP)
- **capabilities.json** - Feature flags and supported capabilities