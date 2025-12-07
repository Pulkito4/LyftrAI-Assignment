"""Unified HTML→Section parser for both static and dynamic scrapers."""

__all__ = ["parse_html", "extract_meta"]

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag, NavigableString

from backend.models import Section, Content, LinkItem, ImageItem, Meta
from backend.config import (
    MAX_RAW_HTML_LENGTH,
    NOISE_SELECTORS,
    SECTION_TYPE_KEYWORDS,
)


def _safe_extract(extractor_func, default=""):
    """Helper to extract data with fallback on failure."""
    try:
        result = extractor_func()
        return result.strip() if result else default
    except (AttributeError, TypeError, KeyError, IndexError):
        return default


def extract_meta(html: str, url: str, strategy: str = None) -> Meta:
    """Extracts page metadata (title, description, language, canonical, strategy)."""
    soup = BeautifulSoup(html, "lxml")

    title = (
        _safe_extract(lambda: soup.find("title").get_text())
        or _safe_extract(lambda: soup.find("meta", property="og:title")["content"])
        or "Untitled"
    )

    description = _safe_extract(
        lambda: soup.find("meta", attrs={"name": "description"})["content"]
    ) or _safe_extract(lambda: soup.find("meta", property="og:description")["content"])

    language = _safe_extract(
        lambda: soup.find("html")["lang"].split("-")[0], default="en"
    )

    canonical = _safe_extract(
        lambda: soup.find("link", rel="canonical")["href"], default=None
    )

    return Meta(
        title=title,
        description=description,
        language=language,
        canonical=canonical,
        strategy=strategy,
    )


def clean_html(soup: BeautifulSoup) -> None:
    """Removes noise (scripts, styles, ads, modals, cookie banners) in-place."""
    for selector in NOISE_SELECTORS:
        for element in soup.select(selector):
            element.decompose()

    # Remove script and style tags
    for tag in soup.find_all(["script", "style", "noscript"]):
        tag.decompose()


def classify_section_type(element: Tag) -> str:
    """Classifies section type: hero, nav, footer, pricing, faq, list, grid, or unknown."""
    # Get element info
    tag_name = element.name.lower() if element.name else ""
    class_str = " ".join(element.get("class", [])).lower()
    id_str = (element.get("id") or "").lower()

    # Check against keywords
    for section_type, keywords in SECTION_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in f"{tag_name} {class_str} {id_str}":
                return section_type

    # Default based on tag
    if tag_name == "nav":
        return "nav"
    elif tag_name == "footer":
        return "footer"
    elif tag_name == "header" or "hero" in f"{class_str} {id_str}":
        return "hero"
    elif tag_name in ["article", "section"]:
        return "section"

    return "unknown"


def generate_label(element: Tag, section_type: str) -> str:
    """
    Generate a human-readable label for the section.
    Uses heading text if available, otherwise first 5-7 words of the text.
    """
    # 1. Try to find a heading (h1-h6)
    heading = element.find(["h1", "h2", "h3", "h4", "h5", "h6"])
    if heading:
        text = heading.get_text(strip=True)
        if text:
            # Truncate to ~50 chars
            return text[:50] + ("..." if len(text) > 50 else "")

    # 2. Derive from first 5-7 words of text content
    # Use get_text with a separator to preserve some structure but avoid duplication
    text = element.get_text(separator=" ", strip=True)
    if text:
        # Clean up whitespace
        text = re.sub(r"\s+", " ", text)
        words = text.split()[:7]
        label = " ".join(words)
        if len(words) >= 7 or len(text) > len(label):
            label += "..."
        return label[:50]

    # 3. Fallback to section type
    return f"{section_type.capitalize()} Section"


def extract_headings(element: Tag) -> list[str]:
    """Extract all heading texts (h1-h6) from the element"""
    headings = []
    for tag in element.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text = tag.get_text(strip=True)
        if text:
            headings.append(text)
    return headings


def extract_text(element: Tag) -> str:
    """
    Extract clean text content from the element.
    Removes extra whitespace and joins paragraphs.
    Skips content inside tables (as they are extracted separately).
    If the content is mostly links (>60%), returns empty string to avoid redundancy.
    """

    def get_text_skipping_tags(el, tags_to_skip):
        texts = []
        for child in el.children:
            if isinstance(child, NavigableString):
                t = child.strip()
                if t:
                    texts.append(t)
            elif isinstance(child, Tag):
                if child.name in tags_to_skip:
                    continue
                texts.append(get_text_skipping_tags(child, tags_to_skip))
        return " ".join(texts)

    # Extract text skipping tables
    text = get_text_skipping_tags(element, ["table"])

    # Clean up whitespace
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return ""

    # Check link density
    # Calculate length of text inside links
    link_text_len = 0
    for a in element.find_all("a"):
        # Only count links that are NOT inside tables (since we already skipped tables)
        if not a.find_parent("table"):
            link_text_len += len(a.get_text(strip=True))

    # Calculate density
    if len(text) > 0:
        density = link_text_len / len(text)
        # If more than 60% of the text is links, it's likely a link list/nav
        if density > 0.6:
            return ""

    return text


def extract_links(element: Tag, base_url: str) -> list[LinkItem]:
    """
    Extract all links from the element and make them absolute URLs.
    """
    links = []
    seen_hrefs = set()

    for a_tag in element.find_all("a", href=True):
        href = a_tag["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        # Make absolute URL
        absolute_url = urljoin(base_url, href)

        # Avoid duplicates
        if absolute_url in seen_hrefs:
            continue
        seen_hrefs.add(absolute_url)

        # Get link text
        text = a_tag.get_text(strip=True) or absolute_url

        links.append(LinkItem(text=text, href=absolute_url))

    return links


def extract_images(element: Tag, base_url: str) -> list[ImageItem]:
    """
    Extract all images from the element and make src absolute URLs.
    """
    images = []
    seen_srcs = set()

    for img_tag in element.find_all("img"):
        src = img_tag.get("src") or img_tag.get("data-src", "")
        if not src:
            continue

        src = src.strip()

        # Make absolute URL
        absolute_url = urljoin(base_url, src)

        # Avoid duplicates
        if absolute_url in seen_srcs:
            continue
        seen_srcs.add(absolute_url)

        # Get alt text
        alt = img_tag.get("alt", "").strip()

        images.append(ImageItem(src=absolute_url, alt=alt))

    return images


def extract_lists(element: Tag) -> list[list[str]]:
    """
    Extract all lists (ul, ol) as nested list structure.
    Each list becomes a List[str] of its items.
    """
    lists = []

    for list_tag in element.find_all(["ul", "ol"], recursive=True):
        # Skip nested lists (they'll be processed separately)
        if list_tag.find_parent(["ul", "ol"]):
            continue

        items = []
        for li in list_tag.find_all("li", recursive=False):
            text = li.get_text(strip=True)
            if text:
                items.append(text)

        if items:
            lists.append(items)

    return lists


def extract_tables(element: Tag) -> list[dict]:
    """
    Extract tables as list of dicts with headers and rows.
    """
    tables = []

    for table_tag in element.find_all("table"):
        table_data = {"headers": [], "rows": []}

        # Extract headers
        thead = table_tag.find("thead")
        if thead:
            header_row = thead.find("tr")
            if header_row:
                table_data["headers"] = [
                    th.get_text(strip=True) for th in header_row.find_all(["th", "td"])
                ]

        # Extract rows
        tbody = table_tag.find("tbody") or table_tag
        for tr in tbody.find_all("tr"):
            # Skip header rows
            if tr.find_parent("thead"):
                continue

            row = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if row:
                table_data["rows"].append(row)

        if table_data["headers"] or table_data["rows"]:
            tables.append(table_data)

    return tables


def truncate_html(html: str, max_length: int = MAX_RAW_HTML_LENGTH) -> tuple[str, bool]:
    """
    Truncate HTML to max_length characters.
    Returns (truncated_html, was_truncated)
    """
    if len(html) <= max_length:
        return html, False

    return html[:max_length] + "...", True


def extract_content(element: Tag, base_url: str) -> Content:
    """
    Extract all content from an element into a Content object.
    """
    return Content(
        headings=extract_headings(element),
        text=extract_text(element),
        links=extract_links(element, base_url),
        images=extract_images(element, base_url),
        lists=extract_lists(element),
        tables=extract_tables(element),
    )


def group_by_landmarks(soup: BeautifulSoup, base_url: str) -> list[Section]:
    """
    Group content into sections using HTML5 landmarks (header, nav, main, section, article, footer).
    """
    sections = []
    section_counter = 0

    # Find landmark elements
    landmarks = soup.find_all(
        ["header", "nav", "main", "section", "article", "aside", "footer"]
    )

    for element in landmarks:
        # Skip if this element is inside another landmark (avoid nesting)
        if element.find_parent(
            ["header", "nav", "main", "section", "article", "footer"]
        ):
            continue

        section_type = classify_section_type(element)
        label = generate_label(element, section_type)

        # Generate section ID
        section_id = f"{section_type}-{section_counter}"
        section_counter += 1

        # Extract content
        content = extract_content(element, base_url)

        # Skip empty sections
        if (
            not content.text
            and not content.headings
            and not content.links
            and not content.tables
            and not content.images
        ):
            continue

        # Get raw HTML
        raw_html = str(element)
        raw_html, truncated = truncate_html(raw_html)

        sections.append(
            Section(
                id=section_id,
                type=section_type,
                label=label,
                sourceUrl=base_url,
                content=content,
                rawHtml=raw_html,
                truncated=truncated,
            )
        )

    return sections


def group_by_headings(soup: BeautifulSoup, base_url: str) -> list[Section]:
    """
    Group content into sections using headings (h1-h3).
    Everything between two headings becomes a section.
    """
    sections = []
    section_counter = 0

    # Find all top-level headings
    headings = soup.find_all(["h1", "h2", "h3"])

    for i, heading in enumerate(headings):
        # Get all siblings until next heading
        content_elements = []
        current = heading.next_sibling

        while current:
            # Stop at next heading of same or higher level
            if isinstance(current, Tag) and current.name in ["h1", "h2", "h3"]:
                break

            if isinstance(current, Tag):
                content_elements.append(current)

            current = current.next_sibling

        # Create a wrapper for this section
        wrapper = soup.new_tag("div")
        wrapper.append(heading)
        for elem in content_elements:
            # Clone the element to avoid modifying original
            wrapper.append(elem)

        section_type = "section"
        label = heading.get_text(strip=True)[:50]

        section_id = f"heading-section-{section_counter}"
        section_counter += 1

        content = extract_content(wrapper, base_url)

        # Skip empty sections
        if (
            not content.text
            and not content.headings
            and not content.links
            and not content.tables
            and not content.images
        ):
            continue

        raw_html = str(wrapper)
        raw_html, truncated = truncate_html(raw_html)

        sections.append(
            Section(
                id=section_id,
                type=section_type,
                label=label,
                sourceUrl=base_url,
                content=content,
                rawHtml=raw_html,
                truncated=truncated,
            )
        )

    return sections


def parse_html(html: str, url: str) -> list[Section]:
    """
    Main parsing function - converts HTML to list of Sections.
    This is the unified parser used by both static and dynamic scrapers.

    Strategy:
    1. Clean HTML (remove noise)
    2. Try landmark-based grouping
    3. If insufficient, fallback to heading-based grouping
    4. If still insufficient, create single section from main content

    Args:
        html: Raw HTML string
        url: Source URL for making links absolute

    Returns:
        List of Section objects
    """
    soup = BeautifulSoup(html, "lxml")

    # Clean noise
    clean_html(soup)

    # Try landmark-based grouping first
    sections = group_by_landmarks(soup, url)

    # If we got good sections, return them
    if len(sections) >= 2:
        return sections

    # Fallback to heading-based grouping
    sections = group_by_headings(soup, url)

    # If still insufficient, create a single section from body/main
    if not sections:
        main_element = soup.find("main") or soup.find("body") or soup

        content = extract_content(main_element, url)

        # Only create section if there's actual content
        if (
            content.text
            or content.headings
            or content.links
            or content.tables
            or content.images
        ):
            raw_html = str(main_element)[:MAX_RAW_HTML_LENGTH]
            raw_html, truncated = truncate_html(raw_html)

            sections.append(
                Section(
                    id="main-content-0",
                    type="section",
                    label=generate_label(main_element, "section"),
                    sourceUrl=url,
                    content=content,
                    rawHtml=raw_html,
                    truncated=truncated,
                )
            )

    return sections
