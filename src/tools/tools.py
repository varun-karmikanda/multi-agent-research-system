from langchain.tools import tool
import requests
from src.config import settings
import os
from tavily import TavilyClient
from bs4 import BeautifulSoup
from readability import Document
import trafilatura
import re
from langchain.tools import tool

MAX_CHARS = 2500  # ~600 tokens per page

tavily = TavilyClient(api_key=settings.tavily_api_key.get_secret_value())

@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web and return titles, URLs, and short result snippets."""
    results = tavily.search(query=query, max_results=max_results)
        
    out = [
        f"Title: {res.get('title', 'N/A')}\n"
        f"URL: {res.get('url', 'N/A')}\n"
        f"Snippet: {res.get('content', '')[:300]}"
        for res in results.get('results', [])
    ]
    
    return "\n---\n".join(out)

@tool
def scrape_url(url: str) -> str:
    """
    Scrape one web page using its complete URL.
    Call this tool with exactly one argument, ``url``. Do not pass a query,
    search options, or any other arguments.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }

    try:
        # Request with timeout and strict handling
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        # Handle charset encoding automatically (prevents weird mangled text)
        if response.encoding is None or response.encoding == "ISO-8859-1":
            response.encoding = response.apparent_encoding

        html = response.text

        # ── Strategy 1: Trafilatura (Best for articles & blogs) ─────────
        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False
        )

        if extracted and len(extracted.strip()) > 200:
            return re.sub(r"\s+", " ", extracted).strip()[:MAX_CHARS]

        # ── Strategy 2: Readability + BeautifulSoup ─────────────────────
        doc = Document(html)
        clean_html = doc.summary()
        soup = BeautifulSoup(clean_html, "lxml")  # 'lxml' is faster than 'html.parser'

        _clean_unwanted_tags(soup)
        text = soup.get_text(separator=" ", strip=True)

        if text and len(text) > 200:
            return re.sub(r"\s+", " ", text).strip()[:MAX_CHARS]

        # ── Strategy 3: Fallback Full Page Extraction ───────────────────
        full_soup = BeautifulSoup(html, "lxml")
        _clean_unwanted_tags(full_soup)
        
        fallback_text = full_soup.get_text(separator=" ", strip=True)
        cleaned = re.sub(r"\s+", " ", fallback_text).strip()

        return cleaned[:MAX_CHARS] if cleaned else "Could not extract meaningful content from the page."

    except requests.exceptions.Timeout:
        return "Error: Request timed out while scraping the URL."
    except requests.exceptions.HTTPError as e:
        return f"Error: HTTP failure occurred ({e})"
    except Exception as e:
        return f"Error: Could not scrape URL ({e})"


def _clean_unwanted_tags(soup: BeautifulSoup) -> None:
    """Helper to remove noise tags from HTML trees in-place."""
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript"]):
        tag.decompose()
