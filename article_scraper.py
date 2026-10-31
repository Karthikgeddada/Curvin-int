"""Full-article scraper — the Tier-2 "deep read" for Curvin Intelligence.

Follows article links from Google News RSS and extracts the main body text so
sentiment, the AI analyst report, and chat reason over the FULL article
instead of just the headline + snippet.

Design guarantees (never break the pipeline):
- Every failure returns None and the article falls back to headline+snippet.
- Short time-outs, small byte caps, parallel fetching, zero exceptions leak.

Streamlit-free and torch-free — shared by both the Streamlit app and the
FastAPI web backend.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("article_scraper")

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 8          # seconds per article — keep the pipeline snappy
MAX_HTML_BYTES = 2_000_000   # 2 MB HTML cap per article
MIN_TEXT_CHARS = 400         # below this it's boilerplate/paywall → give up
MAX_TEXT_CHARS = 20_000      # cap what we store per article (deep-read bodies)


def resolve_publisher_url(url: str) -> str | None:
    """
    Decodes new-style Google News redirect URLs (news.google.com/rss/articles/...)
    to the real publisher URL via the batchexecute RPC. Returns the original URL
    when it already points at the publisher, and None when decoding fails.
    """
    if not url or not str(url).startswith(("http://", "https://")):
        return None
    if "news.google.com" not in url:
        return url  # already a direct link

    try:
        from googlenewsdecoder import gnewsdecoder

        res = gnewsdecoder(url, interval=0)
        if isinstance(res, dict) and res.get("success"):
            return res.get("decoded_url")
    except Exception as e:
        logger.debug(f"Redirect decode failed for {url[:80]}: {type(e).__name__}: {e}")
    return None


def scrape_article_text(url: str) -> str | None:
    """Resolves the link (Google News redirect → publisher) and extracts main text.

    Returns None on ANY failure (blocked, paywalled, timeout, non-HTML,
    too-short text) — callers fall back to the headline + snippet.
    """
    if not url or not str(url).startswith(("http://", "https://")):
        return None

    real_url = resolve_publisher_url(url)
    if not real_url:
        return None

    try:
        resp = requests.get(
            real_url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        if resp.status_code != 200:
            return None
        if "text/html" not in resp.headers.get("Content-Type", ""):
            return None

        soup = BeautifulSoup(resp.content[:MAX_HTML_BYTES], "lxml")

        # Strip non-content chrome before extracting text
        for tag in soup(
            ["script", "style", "nav", "header", "footer", "aside", "form", "noscript", "iframe"]
        ):
            tag.decompose()

        # Prefer semantic containers, fall back to all paragraphs
        container = soup.find("article") or soup.find("main") or soup.body or soup
        paragraphs = container.find_all("p")
        text = " ".join(p.get_text(" ").strip() for p in paragraphs)
        text = " ".join(text.split())

        # Too short → nav junk / paywall stub; treat as failure
        if len(text) < MIN_TEXT_CHARS:
            return None
        return text[:MAX_TEXT_CHARS]

    except Exception as e:
        logger.debug(f"Scrape failed for {url[:80]}: {type(e).__name__}: {e}")
        return None


def deep_read_articles(
    news_df: pd.DataFrame,
    limit: int = 15,
    max_workers: int = 8,
) -> pd.DataFrame:
    """
    Deep-reads the top `limit` articles (rows are newest-first after fetch).

    Adds two columns and overwrites `full_text` for successfully scraped rows:
    - deep_text:      extracted article body ("" when not scraped)
    - has_full_text:  True when the full body was captured
    - full_text:      becomes title + body for deep rows (feeds sentiment)

    Failures are silent by design — the row keeps its headline + snippet.
    """
    df = news_df.reset_index(drop=True).copy()
    df["deep_text"] = ""
    df["has_full_text"] = False

    if limit <= 0 or df.empty or "link" not in df.columns:
        return df

    target = df.head(limit)
    results: dict[int, str | None] = {}

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(scrape_article_text, str(url)): idx
                for idx, url in target["link"].items()
            }
            for fut in as_completed(futures):
                idx = futures[fut]
                try:
                    results[idx] = fut.result()
                except Exception:
                    results[idx] = None
    except Exception as e:
        logger.warning(f"Deep-read thread pool failed entirely: {e}")
        return df

    ok = 0
    for idx, text in results.items():
        if text:
            df.at[idx, "deep_text"] = text
            df.at[idx, "has_full_text"] = True
            df.at[idx, "full_text"] = f"{df.at[idx, 'title']}\n\n{text}"
            ok += 1

    logger.info(f"Deep read: {ok}/{len(results)} full articles captured.")
    return df
