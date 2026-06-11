"""
LangChain tool definitions used by the vendor-risk ReAct agent.
Each tool is decorated with @tool and returns a plain string so that
the LLM can parse and reason over the results.
"""
from __future__ import annotations
import json
import time
import urllib.parse
import re
from typing import Optional

import httpx
import feedparser
from langchain_core.tools import tool

try:
    from duckduckgo_search import DDGS
    _DDG_AVAILABLE = True
except ImportError:
    _DDG_AVAILABLE = False


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_text(raw: str, max_chars: int = 800) -> str:
    """Strip HTML tags and truncate."""
    clean = re.sub(r"<[^>]+>", " ", raw)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:max_chars]


def _ddg_search(query: str, max_results: int = 5) -> list[dict]:
    """Run a DuckDuckGo text search; fall back gracefully."""
    if not _DDG_AVAILABLE:
        return []
    try:
        with DDGS() as ddg:
            results = list(ddg.text(query, max_results=max_results))
        return results
    except Exception as exc:
        return [{"title": "Search error", "body": str(exc), "href": ""}]


# ── Tool 1 – General Web Search ───────────────────────────────────────────────

@tool
def web_search(query: str) -> str:
    """
    Search the public web for information about a vendor.
    Use this for general company news, recent events, controversies, and
    background information.  Input should be a focused search query string.
    Returns a JSON list of {title, snippet, url} objects.
    """
    results = _ddg_search(query, max_results=6)
    output = []
    for r in results:
        output.append({
            "title": r.get("title", ""),
            "snippet": _safe_text(r.get("body", ""), 600),
            "url": r.get("href", ""),
        })
    if not output:
        return json.dumps([{"title": "No results", "snippet": "Could not retrieve web results.", "url": ""}])
    return json.dumps(output, ensure_ascii=False)


# ── Tool 2 – Financial News Feed ──────────────────────────────────────────────

@tool
def financial_news_search(vendor_name: str) -> str:
    """
    Retrieve the latest financial news for the vendor from RSS feeds
    (Reuters, Bloomberg RSS mirrors, Yahoo Finance).
    Use this to surface earnings reports, credit events, downgrades,
    debt issues, or M&A activity.
    Returns a JSON list of {title, summary, published, source} objects.
    """
    feeds = [
        f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={urllib.parse.quote(vendor_name)}&region=US&lang=en-US",
        f"https://news.google.com/rss/search?q={urllib.parse.quote(vendor_name + ' oil financial')}&hl=en-US&gl=US&ceid=US:en",
    ]
    items = []
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:4]:
                items.append({
                    "title": entry.get("title", ""),
                    "summary": _safe_text(entry.get("summary", ""), 400),
                    "published": entry.get("published", ""),
                    "source": feed.feed.get("title", url),
                })
        except Exception:
            continue
        if len(items) >= 6:
            break

    # Supplement with DDG news
    ddg_results = _ddg_search(f"{vendor_name} financial results earnings debt 2024 2025", max_results=4)
    for r in ddg_results:
        items.append({
            "title": r.get("title", ""),
            "summary": _safe_text(r.get("body", ""), 400),
            "published": "",
            "source": "DuckDuckGo News",
        })

    if not items:
        return json.dumps([{"title": "No financial news found", "summary": "", "published": "", "source": ""}])
    return json.dumps(items[:8], ensure_ascii=False)


# ── Tool 3 – Regulatory & Compliance Search ───────────────────────────────────

@tool
def compliance_search(vendor_name: str) -> str:
    """
    Search for regulatory actions, fines, ESG violations, sanctions,
    environmental incidents, or compliance failures associated with the vendor.
    Returns a JSON list of {title, snippet, url} objects.
    """
    queries = [
        f"{vendor_name} regulatory fine penalty SEC CFTC EPA 2023 2024 2025",
        f"{vendor_name} ESG environmental violation compliance breach",
        f"{vendor_name} sanctions OFAC corruption bribery lawsuit",
    ]
    all_results = []
    for q in queries:
        results = _ddg_search(q, max_results=3)
        for r in results:
            all_results.append({
                "title": r.get("title", ""),
                "snippet": _safe_text(r.get("body", ""), 500),
                "url": r.get("href", ""),
            })
        time.sleep(0.3)

    if not all_results:
        return json.dumps([{"title": "No compliance issues found in search", "snippet": "", "url": ""}])
    return json.dumps(all_results[:8], ensure_ascii=False)


# ── Tool 4 – Social Media / X Search ─────────────────────────────────────────

@tool
def social_media_search(vendor_name: str) -> str:
    """
    Search for recent social media signals about the vendor on X (Twitter)
    and Reddit.  Looks for sentiment shifts, viral controversies, supply
    disruption rumours, and protest activity.
    Returns a JSON list of {title, snippet, url, platform} objects.
    """
    queries = [
        f"site:twitter.com OR site:x.com {vendor_name} oil supply risk controversy",
        f"site:reddit.com {vendor_name} oil vendor risk opinion",
        f"{vendor_name} oil social media controversy boycott protest 2025",
    ]
    all_results = []
    for q in queries:
        results = _ddg_search(q, max_results=3)
        for r in results:
            url = r.get("href", "")
            platform = "X/Twitter" if "twitter.com" in url or "x.com" in url else \
                       "Reddit" if "reddit.com" in url else "Web"
            all_results.append({
                "title": r.get("title", ""),
                "snippet": _safe_text(r.get("body", ""), 400),
                "url": url,
                "platform": platform,
            })
        time.sleep(0.3)

    if not all_results:
        return json.dumps([{"title": "No social signals found", "snippet": "", "url": "", "platform": ""}])
    return json.dumps(all_results[:8], ensure_ascii=False)


# ── Tool 5 – YouTube / Video Intelligence ────────────────────────────────────

@tool
def video_intelligence_search(vendor_name: str) -> str:
    """
    Search YouTube and video platforms for documentary footage, analyst
    interviews, investor day recordings, protest coverage, or safety incident
    footage related to the vendor.
    Returns a JSON list of {title, description, url, channel} objects.
    """
    query = f"{vendor_name} oil company risk analysis documentary interview 2024 2025"
    # Use DDG to surface YouTube links
    results = _ddg_search(f"site:youtube.com {query}", max_results=5)
    items = []
    for r in results:
        items.append({
            "title": r.get("title", ""),
            "description": _safe_text(r.get("body", ""), 400),
            "url": r.get("href", ""),
            "channel": "YouTube",
        })

    # Also search for news video coverage
    news_results = _ddg_search(f"{vendor_name} oil spill safety incident video news", max_results=3)
    for r in news_results:
        items.append({
            "title": r.get("title", ""),
            "description": _safe_text(r.get("body", ""), 400),
            "url": r.get("href", ""),
            "channel": "News Video",
        })

    if not items:
        return json.dumps([{"title": "No video content found", "description": "", "url": "", "channel": ""}])
    return json.dumps(items[:6], ensure_ascii=False)


# ── Tool 6 – Geopolitical Risk Search ────────────────────────────────────────

@tool
def geopolitical_risk_search(vendor_name: str) -> str:
    """
    Assess geopolitical risks: country of operations, political instability,
    conflict zones, OPEC+ decisions affecting the vendor, and trade restrictions.
    Returns a JSON list of {title, snippet, url} objects.
    """
    queries = [
        f"{vendor_name} oil geopolitical risk country operations 2024 2025",
        f"{vendor_name} OPEC sanctions trade war supply disruption",
        f"{vendor_name} political instability region conflict operations",
    ]
    all_results = []
    for q in queries:
        results = _ddg_search(q, max_results=3)
        for r in results:
            all_results.append({
                "title": r.get("title", ""),
                "snippet": _safe_text(r.get("body", ""), 500),
                "url": r.get("href", ""),
            })
        time.sleep(0.3)

    if not all_results:
        return json.dumps([{"title": "No geopolitical data found", "snippet": "", "url": ""}])
    return json.dumps(all_results[:8], ensure_ascii=False)


# ── Tool 7 – Operational Incident Search ─────────────────────────────────────

@tool
def operational_incident_search(vendor_name: str) -> str:
    """
    Search for operational disruptions: pipeline failures, refinery outages,
    oil spills, cyber attacks, labour strikes, and supply chain interruptions.
    Returns a JSON list of {title, snippet, url, incident_type} objects.
    """
    queries = [
        f"{vendor_name} oil spill pipeline failure refinery outage 2023 2024 2025",
        f"{vendor_name} cyberattack ransomware operational disruption",
        f"{vendor_name} workers strike labour dispute supply chain",
    ]
    all_results = []
    for q in queries:
        results = _ddg_search(q, max_results=3)
        for r in results:
            title = r.get("title", "").lower()
            incident_type = (
                "Cyber" if any(w in title for w in ["cyber", "hack", "ransom"]) else
                "Environmental" if any(w in title for w in ["spill", "leak", "environ"]) else
                "Labour" if any(w in title for w in ["strike", "worker", "labour", "union"]) else
                "Infrastructure"
            )
            all_results.append({
                "title": r.get("title", ""),
                "snippet": _safe_text(r.get("body", ""), 500),
                "url": r.get("href", ""),
                "incident_type": incident_type,
            })
        time.sleep(0.3)

    if not all_results:
        return json.dumps([{"title": "No operational incidents found", "snippet": "", "url": "", "incident_type": ""}])
    return json.dumps(all_results[:8], ensure_ascii=False)


# ── Export all tools ──────────────────────────────────────────────────────────

ALL_TOOLS = [
    web_search,
    financial_news_search,
    compliance_search,
    social_media_search,
    video_intelligence_search,
    geopolitical_risk_search,
    operational_incident_search,
]
