"""Curvin Intelligence — FastAPI backend for the Vercel/Render web deployment.

Reuses the core pipeline modules (fetch_news, article_scraper, sentiment_gemini,
openrouter_client, ai_analyst, chat_with_news) without any Streamlit/torch dependencies, so the
Render service stays light (see requirements-web.txt).
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv(override=True)

from article_scraper import deep_read_articles
from fetch_news import LAST_FETCH_DIAGNOSTICS, fetch_industry_news
from sentiment_gemini import apply_gemini_sentiment_to_news, gemini_available
from news_store import fetch_history, store_articles, store_enabled
from ai_analyst import MarketAnalyst
from chat_with_news import NewsChat

app = FastAPI(
    title="Curvin Intelligence",
    description="AI Market Intelligence Platform API — news, sentiment, analyst reports, chat",
)

# CORS: the Vercel frontend calls this API cross-origin. Without this the
# browser blocks every request ("Failed to fetch").
# ALLOWED_ORIGIN env: "*" (default) allows all origins; a comma-separated
# list (e.g. "https://your-app.vercel.app") locks it down.
_allowed_origin = os.getenv("ALLOWED_ORIGIN", "*")
_origins = [o.strip().rstrip("/") for o in _allowed_origin.split(",") if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _openrouter_keys() -> list:
    """Collects the OpenRouter API key from the environment (single-key setup)."""
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    return [key] if key else []


# ── Request schemas ──────────────────────────────────────────────────────
class FetchRequest(BaseModel):
    industry: str
    region: str = "United States"
    max_articles: int = Field(default=50, ge=1, le=500)


class Article(BaseModel):
    title: str
    description: str = ""
    article_text: str = ""  # full deep-read article body (optional)


class ReportRequest(BaseModel):
    industry: str
    articles: list[Article]


class ChatRequest(BaseModel):
    query: str
    articles: list[Article]
    industry: str = ""  # when set, chat also blends in stored history
    history: list | None = None


# ── API endpoints ────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    """Liveness + configuration probe (used by the frontend and Render)."""
    return {
        "status": "ok",
        "version": "2.1.0-bing-fallback",
        "sentiment_provider": "gemini" if gemini_available() else "unconfigured",
        "llm_ready": bool(_openrouter_keys()),
    }


@app.post("/api/fetch")
def fetch_and_score(req: FetchRequest):
    """Stage 1+2 of the pipeline: news ingestion + Gemini sentiment scoring."""
    try:
        news_df = fetch_industry_news(req.industry, req.max_articles, req.region)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"News fetch failed: {e}")

    if news_df.empty:
        diag = "; ".join(LAST_FETCH_DIAGNOSTICS) or "no source attempts recorded"
        raise HTTPException(
            status_code=404,
            detail=f"No articles found for this industry and region. Sources tried: {diag}",
        )

    # Sentiment runs on the Gemini API — torch/FinBERT is intentionally NOT
    # shipped to Render (see requirements-web.txt).
    if not gemini_available():
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured on the server. "
            "Set it in the Render dashboard environment variables.",
        )

    # Tier-2 deep read: fetch full article bodies for the top N articles so
    # sentiment + report/chat reason over real content, not just headlines.
    # Best effort — failures fall back to headline + snippet silently.
    deep_limit = int(os.getenv("DEEP_READ_LIMIT", "15"))
    if deep_limit > 0:
        try:
            news_df = deep_read_articles(news_df, limit=deep_limit)
        except Exception:
            pass  # never break the fetch over scraping

    try:
        enriched = apply_gemini_sentiment_to_news(news_df)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Sentiment engine error: {e}")

    # Sanitize columns: ship the deep-read body as article_text (capped),
    # drop the bulky internal full_text/deep_text columns.
    enriched = enriched.reset_index(drop=True)
    articles = [
        {
            "title": row["title"],
            "link": row.get("link", ""),
            "published": str(row.get("published", "")),
            "source": row.get("source", ""),
            "description": row.get("description", ""),
            "sentiment": row.get("sentiment", "Neutral"),
            "confidence": float(row.get("confidence", 0.0) or 0.0),
            "has_full_text": bool(row.get("has_full_text", False)),
            "article_text": (row.get("deep_text", "") or "")[:8000],
        }
        for _, row in enriched.iterrows()
    ]

    # Persist the scored fetch to Postgres (Supabase) — best effort
    stored = store_articles(enriched, req.industry, req.region) if store_enabled() else 0

    return {
        "industry": req.industry,
        "region": req.region,
        "count": len(articles),
        "stored": stored,
        "articles": articles,
    }


@app.get("/api/history")
def history(
    industry: str = Query(..., description="Industry to pull stored history for"),
    days: int = Query(7, ge=1, le=365),
    limit: int = Query(30, ge=1, le=200),
):
    """Persistent market history from the Postgres store (Supabase)."""
    if not store_enabled():
        raise HTTPException(
            status_code=503,
            detail="DATABASE_URL is not configured on the server. "
            "Create a Supabase project and set its connection pooling URI "
            "(Project Settings → Database).",
        )
    df = fetch_history(industry, limit=limit, days=days)
    articles = [
        {
            "title": row["title"],
            "link": row.get("link") or "",
            "published": str(row.get("published") or ""),
            "source": row.get("source") or "",
            "description": row.get("description") or "",
            "sentiment": row.get("sentiment") or "",
            "confidence": float(row.get("confidence") or 0.0),
            "has_full_text": bool(row.get("full_text")),
            "article_text": (row.get("full_text") or "")[:8000],
            "fetched_at": str(row.get("fetched_at") or ""),
        }
        for _, row in df.iterrows()
    ]
    return {"industry": industry, "days": days, "count": len(articles), "articles": articles}


@app.post("/api/report")
def analyst_report(req: ReportRequest):
    """LLM-generated institutional analyst report (OpenRouter LLaMA 3.3 70B)."""
    keys = _openrouter_keys()
    if not keys:
        raise HTTPException(
            status_code=503,
            detail="OPENROUTER_API_KEY is not configured on the server. "
            "Set it in the Render dashboard environment variables.",
        )

    analyst = MarketAnalyst(keys)
    # Deep-read articles carry the full body in article_text — prefer it
    # over the headline snippet when building the report context.
    articles = [
        {
            "title": a.title,
            "description": a.article_text[:6000] if a.article_text else a.description,
        }
        for a in req.articles[:15]
    ]
    report = analyst.generate_sector_report(req.industry, articles)
    return report


@app.post("/api/chat")
def chat(req: ChatRequest):
    """RAG-lite chat grounded in the provided news context."""
    keys = _openrouter_keys()
    if not keys:
        raise HTTPException(
            status_code=503,
            detail="OPENROUTER_API_KEY is not configured on the server. "
            "Set it in the Render dashboard environment variables.",
        )

    engine = NewsChat(keys)
    articles = [
        {
            "title": a.title,
            "description": a.article_text[:6000] if a.article_text else a.description,
        }
        for a in req.articles[:20]
    ]

    # Persistent-history enrichment (Level-1 RAG): when an industry is given,
    # blend in previously stored articles for real multi-session memory.
    if req.industry and store_enabled():
        try:
            seen = {a["title"] for a in articles}
            for _, row in fetch_history(req.industry, limit=30, days=30).iterrows():
                if len(articles) >= 25:
                    break
                if row["title"] in seen:
                    continue
                articles.append(
                    {
                        "title": row["title"],
                        "description": (row.get("full_text") or row.get("description") or "")[:6000],
                    }
                )
                seen.add(row["title"])
        except Exception:
            pass  # history is a bonus, never a requirement

    answer = engine.handle_query(req.query, articles, req.history)
    return {"answer": answer}


# Serve the static web UI from webui/ (index.html at /, assets alongside).
# Mounted AFTER the API routes so /api/* is matched first.
_WEBUI_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webui"
)
app.mount("/", StaticFiles(directory=_WEBUI_DIR, html=True), name="webui")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
