"""Postgres-backed news persistence — the Level-1 RAG store for Curvin Intelligence.

Works with any Postgres (built for Supabase's free tier). Every fetch stores
its scored articles, so market history survives Render restarts and app
sleeps. Retrieval is keyword/full-text based — deliberately NO vector search
(the corpus per industry is small; full-text covers it).

Rules (never break the pipeline):
- Everything is gated on DATABASE_URL. No URL → store disabled, zero impact.
- The schema auto-creates itself on first connection (no SQL to run by hand).
- Every function fails silently and returns 0 / an empty DataFrame.

Streamlit-free — shared by the Streamlit app and the FastAPI web backend.
"""

import logging
import os

import pandas as pd

logger = logging.getLogger("news_store")

# Auto-created on first connect. UNIQUE(title, industry) makes repeated
# fetches upsert instead of duplicating; the GIN index enables full-text search.
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS articles (
    id          BIGSERIAL PRIMARY KEY,
    industry    TEXT        NOT NULL,
    region      TEXT        NOT NULL DEFAULT 'Global',
    title       TEXT        NOT NULL,
    link        TEXT,
    published   TEXT,
    source      TEXT,
    description TEXT,
    full_text   TEXT,
    sentiment   TEXT,
    confidence  REAL,
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (title, industry)
);
CREATE INDEX IF NOT EXISTS idx_articles_industry_time
    ON articles (industry, fetched_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_fts
    ON articles USING gin (to_tsvector('english', title || ' ' || COALESCE(description, '')));
"""


def store_enabled() -> bool:
    """True when a Postgres DATABASE_URL is configured."""
    return bool(os.getenv("DATABASE_URL", "").strip())


def _connect():
    """Opens a short-lived SSL Postgres connection (safe for Render free tier)."""
    import psycopg2

    conn = psycopg2.connect(
        os.getenv("DATABASE_URL").strip(),
        sslmode="require",       # Supabase requires SSL
        connect_timeout=8,
    )
    conn.autocommit = True
    return conn


def _ensure_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(_SCHEMA_SQL)


def store_articles(news_df: pd.DataFrame, industry: str, region: str = "Global") -> int:
    """
    Upserts the scored articles for one fetch into Postgres.

    Returns the number of rows attempted (0 when disabled or on ANY failure —
    persistence is best-effort and never blocks the pipeline).
    """
    if not store_enabled() or news_df is None or news_df.empty:
        return 0

    rows = []
    for _, r in news_df.iterrows():
        deep = str(r.get("deep_text", "") or "") if r.get("has_full_text") else ""
        rows.append(
            (
                str(industry)[:200],
                str(region)[:200],
                str(r.get("title", ""))[:1000],
                str(r.get("link", "") or "")[:2000],
                str(r.get("published", "") or "")[:100],
                str(r.get("source", "") or "")[:200],
                str(r.get("description", "") or "")[:4000],
                deep[:20000],
                str(r.get("sentiment", "") or "")[:20],
                float(r.get("confidence", 0.0) or 0.0),
            )
        )

    try:
        conn = _connect()
        try:
            _ensure_schema(conn)
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO articles (industry, region, title, link, published,
                                          source, description, full_text,
                                          sentiment, confidence)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (title, industry) DO UPDATE SET
                        region     = EXCLUDED.region,
                        link       = EXCLUDED.link,
                        published  = EXCLUDED.published,
                        source     = EXCLUDED.source,
                        description = EXCLUDED.description,
                        full_text  = CASE WHEN EXCLUDED.full_text <> ''
                                          THEN EXCLUDED.full_text
                                          ELSE articles.full_text END,
                        sentiment  = EXCLUDED.sentiment,
                        confidence = EXCLUDED.confidence,
                        fetched_at = now()
                    """,
                    rows,
                )
        finally:
            conn.close()
        logger.info(f"Stored {len(rows)} articles for '{industry}' in Postgres.")
        return len(rows)
    except Exception as e:
        logger.warning(f"Article store failed (continuing without persistence): {e}")
        return 0


def _query_df(sql: str, params: tuple) -> pd.DataFrame:
    """Runs a SELECT and returns a DataFrame (empty on any failure)."""
    try:
        conn = _connect()
        try:
            _ensure_schema(conn)
            with conn.cursor() as cur:
                cur.execute(sql, params)
                cols = [d[0] for d in cur.description]
                return pd.DataFrame(cur.fetchall(), columns=cols)
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"History query failed: {e}")
        return pd.DataFrame()


def fetch_history(industry: str, limit: int = 30, days: int = 30) -> pd.DataFrame:
    """
    Recent stored articles for an industry, newest first.
    Empty DataFrame when persistence is disabled or the query fails.
    """
    if not store_enabled():
        return pd.DataFrame()
    return _query_df(
        """
        SELECT title, link, published, source, description, full_text,
               sentiment, confidence, fetched_at
        FROM articles
        WHERE industry = %s
          AND fetched_at >= now() - (%s * INTERVAL '1 day')
        ORDER BY fetched_at DESC
        LIMIT %s
        """,
        (industry, days, limit),
    )


def search_articles(query: str, industry: str | None = None, limit: int = 20) -> pd.DataFrame:
    """
    Keyword/full-text search over ALL stored history (optional industry
    filter). Empty DataFrame when disabled, empty, or failed.
    """
    if not store_enabled() or not (query or "").strip():
        return pd.DataFrame()

    like = f"%{query.strip()}%"
    sql = """
        SELECT title, link, published, source, description, full_text,
               sentiment, confidence, fetched_at
        FROM articles
        WHERE (to_tsvector('english', title || ' ' || COALESCE(description, ''))
               @@ websearch_to_tsquery('english', %s)
               OR title ILIKE %s
               OR COALESCE(description, '') ILIKE %s)
    """
    params: list = [query.strip(), like, like]
    if industry:
        sql += " AND industry = %s"
        params.append(str(industry)[:200])
    sql += " ORDER BY fetched_at DESC LIMIT %s"
    params.append(limit)
    return _query_df(sql, tuple(params))
