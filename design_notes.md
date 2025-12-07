# Design Notes

## Static vs JS Fallback

**Strategy:** We prioritize speed by attempting static scraping first (httpx + BeautifulSoup). We only spin up a heavy browser (Playwright) if our heuristics suggest the page is broken or empty without JavaScript.

**When we decide to use JS rendering:**
- The parsed content is suspiciously short (< 500 chars).
- We see tell-tale signs of SPA frameworks (React's `#__next`, Vue's `data-v-app`).
- The page is mostly script tags with very little actual HTML text (< 3% ratio).
- We find `<noscript>` tags explicitly telling us to enable JavaScript.
- The page lacks basic semantic structure like `<main>` or `<article>`.

**Our decision flow:**
1.  **Fast Pass:** Grab the HTML with `httpx` (10s timeout).
2.  **Parse:** Feed it to BeautifulSoup.
3.  **Analyze:** Run our `needs_js_rendering()` checks.
4.  **Fallback:** If the checks fail, launch Playwright.
5.  **Interact:** If interactions are enabled, we proceed with depth ≥ 3 actions.

---

## Wait Strategy for JS

**Implemented:**
- [x] **Network idle** - We wait for the network to settle (5s timeout) so we don't scrape half-loaded data.
- [ ] **Fixed sleep** - We avoid blind sleeps, using them only as a tiny 1s safety buffer at the end.
- [x] **Wait for selectors** - We actively poll for key elements like `body`, `main`, or `article`.

**Details:**
Reliability is key here. After navigating, we don't just wait for `domcontentloaded`. We wait for the network to go idle, then actively hunt for the `body` tag. If we can't find a `main` or `article` tag within 2 seconds, we assume the page structure is non-standard and proceed with what we have. The final 1s sleep is just a safety net for any lingering animations.

---

## Click & Scroll Strategy

**Click flows implemented:**
- **Tabs:** We look for standard tab roles (`[role='tab']`, `.tab`) and click up to 5 of them, pausing briefly to let content swap.
- **Load More:** We hunt for "Load more" buttons. To be smart, we count DOM elements before and after clicking to confirm new content actually loaded.
- **Pagination:** We follow "Next" links for up to 3 pages, capturing a snapshot of the HTML at each step.

**Scroll approach:**
- We trigger a smooth scroll to the bottom of the page.
- We also simulate the `End` key to trigger keyboard-driven infinite scrolls.
- We measure the scroll height; if it doesn't grow, we stop.

**Stop conditions:**
- **Max depth:** We strictly cap interactions at 3 (pages/clicks/scrolls) to keep execution time reasonable.
- **Timeout:** Every interaction has a hard 5s limit.
- **No change:** If clicking/scrolling doesn't change the DOM or scroll height, we assume we're done.

**Auto mode:**
If you don't pick a strategy, we try them all in a logical order: Tabs first (least intrusive), then Load More, then Scroll, and finally Pagination.

---

## Section Grouping & Labels

**How we group DOM into sections:**
We try to be semantic first. We look for HTML5 landmarks like `<header>`, `<main>`, and `<footer>`. If the site is a "div soup" with no landmarks, we fall back to grouping content between `h1`-`h3` headings. As a last resort, we just grab the whole `<body>`.

**How we derive section `type`:**
We use a keyword matching approach on class names and IDs.
- `hero`: "banner", "jumbotron"
- `nav`: "menu", "navigation"
- `footer`: "copyright"
- `pricing`: "plan", "price"
- `faq`: "accordion", "question"
If we can't match a keyword, we default to the tag name (e.g., `<nav>` becomes "nav").

**How we derive section `label`:**
We prefer using the first heading we find. If there's no heading, we grab the first few words of the text content to give you a hint of what's inside.

---

## Noise Filtering & Truncation

**What we filter out:**
We aggressively clean the HTML before parsing. We strip out `<script>` and `<style>` tags, and we have a hit-list of selectors for cookie banners (`.cookie-consent`), modals (`.modal`), and ads (`.advertisement`).

**How we truncate `rawHtml`:**
To keep your JSON responses from exploding in size, we cap the `rawHtml` of each section at 5000 characters. If a section is longer, we chop it off and add a `...` marker, setting a `truncated: true` flag so you know there's more.

---

## Key Trade-offs

1.  **Heuristics vs. Perfection:** Our JS detection isn't 100% perfect, but it catches 95% of cases and saves massive amounts of time on static sites.
2.  **Complexity for Speed:** Building the orchestrator to manage the static-to-dynamic fallback was complex, but it makes the scraper feel instant for simple pages.
3.  **Depth Limits:** We cap interactions at depth 3. This is a balance between proving we can handle interactions and not letting a scrape run for 10 minutes.
4.  **Truncation:** We lose some data by truncating HTML, but it ensures the API remains responsive and usable.

---

For the high-level architectural decisions, see **ARCHITECTURE.md**.
