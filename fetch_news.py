import time
import feedparser
import pandas as pd
import requests
import logging
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from utils.deduplicator import deduplicate_news

logger = logging.getLogger("fetch_news")

REGION_PARAMS = {
    "United States": "hl=en-US&gl=US&ceid=US:en",
    "United Kingdom": "hl=en-GB&gl=GB&ceid=GB:en",
    "India": "hl=en-IN&gl=IN&ceid=IN:en",
    "Canada": "hl=en-CA&gl=CA&ceid=CA:en",
    "Australia": "hl=en-AU&gl=AU&ceid=AU:en",
    "Global": "hl=en-US&gl=US&ceid=US:en" # Defaults to US edition for general global news
}

_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _http_get(url: str, attempts: int = 3):
    """GET with a browser User-Agent, retries and backoff.
    Returns the response on HTTP 200, else None. Never raises."""
    headers = {"User-Agent": _BROWSER_UA}
    for attempt in range(1, attempts + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return resp
            logger.warning(f"HTTP {resp.status_code} from {url[:90]} (attempt {attempt}/{attempts})")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed (attempt {attempt}/{attempts}): {type(e).__name__}: {str(e)[:120]}")
        if attempt < attempts:
            time.sleep(2 * attempt)
    return None


def _parse_google_feed(content: bytes) -> list:
    """Google News RSS entries -> standard article dicts."""
    rows = []
    for entry in feedparser.parse(content).entries:
        rows.append({
            'title': entry.title,
            'link': entry.link,
            'published': entry.published,
            'source': entry.source.title if 'source' in entry else 'Unknown',
            'description': entry.summary if 'summary' in entry else ''
        })
    return rows


def _parse_bing_feed(content: bytes) -> list:
    """Bing News RSS entries -> standard article dicts (direct publisher links)."""
    rows = []
    for entry in feedparser.parse(content).entries:
        link = entry.link
        try:
            source = urlparse(link).netloc.replace("www.", "")
        except Exception:
            source = 'Unknown'
        rows.append({
            'title': entry.title,
            'link': link,
            'published': entry.get('published', ''),
            'source': source,
            'description': entry.summary if 'summary' in entry else ''
        })
    return rows


def fetch_industry_news(industry: str, max_articles: int = 50, region: str = "United States") -> pd.DataFrame:
    """Fetches real-time news from Google News RSS using a targeted query and sorts by newest first."""
    # Google News RSS returns a maximum of 100 items per feed.
    # To satisfy higher `max_articles` requests (up to 500), we dynamically 
    # append generic suffixes to bypass the per-request limit.
    base_query = f"{industry} industry {region if region != 'Global' else ''}".strip()
    suffixes = ["news", "market updates", "analysis", "latest developments", "business trends"]
    
    # Only use as many queries as we need to approach max_articles (assuming ~100 per query)
    num_queries_needed = min(len(suffixes), max(1, (max_articles // 100) + 1))
    queries = [f"{base_query} {suffixes[i]} when:14d" for i in range(num_queries_needed)]
    
    all_entries = []
    
    # Process each query variation to get a broad range of industry news
    for query in queries:
        encoded_query = requests.utils.quote(query)
        region_param = REGION_PARAMS.get(region, REGION_PARAMS["United States"])
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&{region_param}"
        # Use requests with a User-Agent to bypass Google News bot-blocking
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            response = requests.get(rss_url, headers=headers, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                for entry in feed.entries:
                    all_entries.append({
                        'title': entry.title,
                        'link': entry.link,
                        'published': entry.published,
                        'source': entry.source.title if 'source' in entry else 'Unknown',
                        'description': entry.summary if 'summary' in entry else ''
                    })
            else:
                logger.warning(f"Google News returned HTTP {response.status_code} for query: {query}")
        except requests.exceptions.Timeout:
            logger.warning(f"Request timed out for query: {query}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed for query '{query}': {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching query '{query}': {e}")

            
            # Fast-break if we have enough raw articles for deduplication logic
            if len(all_entries) >= max_articles * 3:
                break
    
    news_df = pd.DataFrame(all_entries)
    
    if news_df.empty:
        return pd.DataFrame(columns=['title', 'link', 'published', 'source', 'description', 'full_text'])
    
    # Sort articles by published date (newest first)
    news_df['published_datetime'] = pd.to_datetime(news_df['published'], errors='coerce')
    news_df = news_df.sort_values(by='published_datetime', ascending=False)
    news_df = news_df.drop(columns=['published_datetime'])
        
    news_df = deduplicate_news(news_df)
    
    # Limit to requested count after deduplication
    news_df = news_df.head(max_articles)
    
    # Text normalization: Cleaning descriptions and combining title/desc for sentiment context
    news_df['description'] = news_df['description'].apply(clean_text)
    news_df['full_text'] = news_df['title'] + " - " + news_df['description']
    
    return news_df

def clean_text(html_content: str) -> str:
    """Removes HTML tags and normalizes whitespace."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "lxml")
    text = soup.get_text()
    return " ".join(text.split())
