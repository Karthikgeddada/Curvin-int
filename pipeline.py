import streamlit as st
import pandas as pd
import os
from fetch_news import fetch_industry_news
from article_scraper import deep_read_articles
from news_store import store_articles, store_enabled
from sentiment_analysis import apply_sentiment_to_news
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("pipeline")

# Tier-2 "deep read": fetch full article bodies for the top N articles so
# sentiment + the AI report/chat reason over real content, not just headlines.
# 0 disables it; failed scrapes silently fall back to headline + snippet.
DEEP_READ_LIMIT = int(os.getenv("DEEP_READ_LIMIT", "15"))

def run_pipeline(industry: str, max_articles: int, region: str = "United States") -> pd.DataFrame | None:
    """
    Orchestrates the full data pipeline:
    1. Fetch news via Google News RSS
    2. Deduplicate + Clean articles
    3. Deep-read the top articles (full bodies, best effort)
    4. Score sentiment via FinBERT or Gemini (provider dispatch)
    5. Return enriched DataFrame
    """
    logger.info(f"Starting pipeline for industry='{industry}', region='{region}', max_articles={max_articles}")
    
    # ── Stage 1: News Ingestion ───────────────────────────────────────────────
    with st.spinner(f"📡 Fetching {max_articles} articles for **{industry}** in **{region}**..."):
        try:
            news_df = fetch_industry_news(industry, max_articles, region)
        except Exception as e:
            logger.error(f"News fetch failed: {e}")
            st.error(f"❌ Failed to fetch news: {e}")
            return None

    if news_df.empty:
        st.warning("⚠️ No articles found for the selected industry and time range.")
        return None
    
    actual_count = len(news_df)
    logger.info(f"Fetched {actual_count} unique articles after deduplication.")

    # ── Stage 1.5: Deep Read (full article bodies) ──────────────────────────
    # Follows the top N article links, decodes the Google News redirects and
    # extracts the full body text. Best effort: failures fall back to the
    # headline + snippet and NEVER break the pipeline.
    if DEEP_READ_LIMIT > 0:
        deep_target = min(DEEP_READ_LIMIT, actual_count)
        with st.spinner(f"📖 Deep-reading the top {deep_target} articles (full text)…"):
            try:
                news_df = deep_read_articles(news_df, limit=deep_target)
                deep_count = int(news_df["has_full_text"].sum())
                logger.info(f"Deep read captured {deep_count}/{deep_target} full articles.")
            except Exception as e:
                logger.warning(f"Deep read failed (falling back to headlines): {e}")

    # ── Stage 2: Sentiment Analysis ───────────────────────────────────────────
    with st.spinner(f"🧠 Running sentiment analysis on {actual_count} articles..."):
        try:
            enriched_df = apply_sentiment_to_news(news_df)
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            st.error(f"❌ Sentiment engine error: {e}")
            return None

    # ── Stage 2.5: Persist to Postgres (Supabase) — best effort ──────────────
    # Market history survives app restarts. Skipped entirely (zero cost)
    # when DATABASE_URL is not configured.
    if store_enabled():
        with st.spinner("💾 Saving to your news history…"):
            try:
                stored = store_articles(enriched_df, industry, region)
                logger.info(f"Stored {stored} articles in Postgres history.")
            except Exception as e:
                logger.warning(f"History store failed (skipping persistence): {e}")

    logger.info("Pipeline complete. Returning enriched DataFrame.")
    return enriched_df
