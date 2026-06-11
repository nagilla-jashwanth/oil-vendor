"""
Tool definitions for the Oil Vendor Risk Management agent system.
Each tool is a proper LangChain BaseTool subclass that can be
wired into LangGraph agent nodes.
"""

import json
import logging
import re
from datetime import datetime
from typing import Optional, Type
import feedparser

import httpx
from duckduckgo_search import DDGS
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Input schemas (Pydantic)
# ---------------------------------------------------------------------------

class WebSearchInput(BaseModel):
    query: str = Field(..., description="Search query string")
    max_results: int = Field(default=8, description="Maximum number of results to return")


class NewsSearchInput(BaseModel):
    company_name: str = Field(..., description="Company or vendor name to search news for")
    focus: str = Field(default="risk financial compliance", description="Focus area for the search")


class SocialMediaSearchInput(BaseModel):
    company_name: str = Field(..., description="Company name to search on social media")
    topic: str = Field(default="controversy risk scandal", description="Topic to focus the social search on")


class YouTubeSearchInput(BaseModel):
    query: str = Field(..., description="YouTube search query")
    max_results: int = Field(default=5, description="Max video results to fetch")


class SECFilingSearchInput(BaseModel):
    company_name: str = Field(..., description="Company name to look up SEC/regulatory filings for")


class RSSFeedInput(BaseModel):
    company_name: str = Field(..., description="Company name to monitor via RSS feeds")


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

class WebSearchTool(BaseTool):
    """Search the web using DuckDuckGo for vendor-related information."""

    name: str = "web_search"
    description: str = (
        "Searches the web for information about an oil vendor. "
        "Use this to find recent news, financial data, regulatory actions, "
        "press releases, and general company information. "
        "Input should be a specific search query."
    )
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str, max_results: int = 8) -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return json.dumps({"results": [], "message": "No results found"})
            formatted = []
            for r in results:
                formatted.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", "")[:400],
                    "url": r.get("href", ""),
                    "source": r.get("source", "")
                })
            return json.dumps({"results": formatted, "count": len(formatted)})
        except Exception as e:
            logger.error(f"WebSearchTool error: {e}")
            return json.dumps({"error": str(e), "results": []})

    async def _arun(self, query: str, max_results: int = 8) -> str:
        return self._run(query, max_results)


class NewsSearchTool(BaseTool):
    """Search for recent news articles about a specific oil vendor."""

    name: str = "news_search"
    description: str = (
        "Fetches recent news articles about an oil vendor from multiple news sources. "
        "Focuses on financial health, operational incidents, regulatory violations, "
        "and reputational events. Returns headlines and summaries."
    )
    args_schema: Type[BaseModel] = NewsSearchInput

    def _run(self, company_name: str, focus: str = "risk financial compliance") -> str:
        try:
            results = []
            queries = [
                f"{company_name} {focus}",
                f"{company_name} SEC fine penalty lawsuit 2024 2025",
                f"{company_name} oil spill accident environmental violation",
                f"{company_name} earnings revenue debt financial results",
            ]
            with DDGS() as ddgs:
                for q in queries:
                    news = list(ddgs.news(q, max_results=4))
                    for item in news:
                        results.append({
                            "title": item.get("title", ""),
                            "body": item.get("body", "")[:350],
                            "url": item.get("url", ""),
                            "date": item.get("date", ""),
                            "source": item.get("source", "")
                        })
            # Deduplicate by URL
            seen = set()
            unique = []
            for r in results:
                if r["url"] not in seen:
                    seen.add(r["url"])
                    unique.append(r)
            return json.dumps({"articles": unique[:20], "count": len(unique)})
        except Exception as e:
            logger.error(f"NewsSearchTool error: {e}")
            return json.dumps({"error": str(e), "articles": []})

    async def _arun(self, company_name: str, focus: str = "risk financial compliance") -> str:
        return self._run(company_name, focus)


class SocialMediaSearchTool(BaseTool):
    """Search social media (X/Twitter via web) for vendor mentions and sentiment."""

    name: str = "social_media_search"
    description: str = (
        "Searches social media and public forums for mentions of an oil vendor. "
        "Looks for whistleblower reports, public controversies, employee complaints, "
        "activist campaigns, and negative sentiment signals. "
        "Covers X (Twitter), Reddit, and public forums."
    )
    args_schema: Type[BaseModel] = SocialMediaSearchInput

    def _run(self, company_name: str, topic: str = "controversy risk scandal") -> str:
        try:
            results = []
            queries = [
                f"site:twitter.com OR site:x.com {company_name} {topic}",
                f"site:reddit.com {company_name} oil vendor risk complaint",
                f"{company_name} whistleblower fraud misconduct allegation",
                f"{company_name} workers strike protest environmental activist",
            ]
            with DDGS() as ddgs:
                for q in queries:
                    items = list(ddgs.text(q, max_results=4))
                    for item in items:
                        results.append({
                            "platform": _detect_platform(item.get("href", "")),
                            "title": item.get("title", ""),
                            "snippet": item.get("body", "")[:300],
                            "url": item.get("href", ""),
                        })
            seen = set()
            unique = [r for r in results if r["url"] not in seen and not seen.add(r["url"])]
            return json.dumps({"posts": unique[:15], "count": len(unique)})
        except Exception as e:
            logger.error(f"SocialMediaSearchTool error: {e}")
            return json.dumps({"error": str(e), "posts": []})

    async def _arun(self, company_name: str, topic: str = "controversy risk scandal") -> str:
        return self._run(company_name, topic)


class YouTubeSearchTool(BaseTool):
    """Search YouTube for documentary and news videos about the vendor."""

    name: str = "youtube_search"
    description: str = (
        "Searches YouTube for videos about an oil vendor including documentaries, "
        "news reports, analyst reviews, and investigative journalism. "
        "Returns video titles, channels, and descriptions as risk signals."
    )
    args_schema: Type[BaseModel] = YouTubeSearchInput

    def _run(self, query: str, max_results: int = 5) -> str:
        try:
            results = []
            yt_queries = [
                f"{query} investigation documentary",
                f"{query} oil spill scandal controversy",
                f"{query} financial crisis debt",
            ]
            with DDGS() as ddgs:
                for q in yt_queries:
                    items = list(ddgs.text(
                        f"site:youtube.com {q}", max_results=max_results
                    ))
                    for item in items:
                        results.append({
                            "title": item.get("title", ""),
                            "description": item.get("body", "")[:250],
                            "url": item.get("href", ""),
                            "channel": _extract_yt_channel(item.get("body", ""))
                        })
            seen = set()
            unique = [r for r in results if r["url"] not in seen and not seen.add(r["url"])]
            return json.dumps({"videos": unique[:12], "count": len(unique)})
        except Exception as e:
            logger.error(f"YouTubeSearchTool error: {e}")
            return json.dumps({"error": str(e), "videos": []})

    async def _arun(self, query: str, max_results: int = 5) -> str:
        return self._run(query, max_results)


class RegulatorySearchTool(BaseTool):
    """Search for SEC filings, regulatory actions, and compliance violations."""

    name: str = "regulatory_search"
    description: str = (
        "Searches for regulatory actions, SEC filings, EPA violations, OSHA incidents, "
        "court cases, and compliance issues for an oil vendor. "
        "Critical for compliance risk assessment."
    )
    args_schema: Type[BaseModel] = SECFilingSearchInput

    def _run(self, company_name: str) -> str:
        try:
            results = []
            queries = [
                f"{company_name} SEC enforcement action fine penalty",
                f"{company_name} EPA violation environmental penalty",
                f"{company_name} OSHA workplace safety violation",
                f"site:sec.gov {company_name} filing 10-K 8-K",
                f"{company_name} regulatory sanction compliance failure 2023 2024 2025",
                f"{company_name} class action lawsuit settlement court",
            ]
            with DDGS() as ddgs:
                for q in queries:
                    items = list(ddgs.text(q, max_results=4))
                    for item in items:
                        results.append({
                            "title": item.get("title", ""),
                            "snippet": item.get("body", "")[:400],
                            "url": item.get("href", ""),
                            "type": _classify_regulatory(item.get("title", "") + " " + item.get("body", ""))
                        })
            seen = set()
            unique = [r for r in results if r["url"] not in seen and not seen.add(r["url"])]
            return json.dumps({"filings": unique[:16], "count": len(unique)})
        except Exception as e:
            logger.error(f"RegulatorySearchTool error: {e}")
            return json.dumps({"error": str(e), "filings": []})

    async def _arun(self, company_name: str) -> str:
        return self._run(company_name)


class FinancialDataTool(BaseTool):
    """Retrieve financial health indicators for an oil vendor."""

    name: str = "financial_data"
    description: str = (
        "Fetches financial health data for an oil vendor: credit ratings, "
        "debt levels, earnings trends, cash flow, bankruptcy risk signals, "
        "stock performance, and analyst downgrades. "
        "Use this to assess financial risk."
    )
    args_schema: Type[BaseModel] = SECFilingSearchInput

    def _run(self, company_name: str) -> str:
        try:
            results = []
            queries = [
                f"{company_name} credit rating downgrade Moody S&P Fitch",
                f"{company_name} debt leverage balance sheet 2024 2025",
                f"{company_name} bankruptcy default financial distress",
                f"{company_name} annual earnings revenue profit loss 2024",
                f"{company_name} stock price analyst target downgrade",
            ]
            with DDGS() as ddgs:
                for q in queries:
                    items = list(ddgs.text(q, max_results=4))
                    for item in items:
                        results.append({
                            "title": item.get("title", ""),
                            "snippet": item.get("body", "")[:400],
                            "url": item.get("href", ""),
                            "category": "financial"
                        })
            seen = set()
            unique = [r for r in results if r["url"] not in seen and not seen.add(r["url"])]
            return json.dumps({"financial_data": unique[:16], "count": len(unique)})
        except Exception as e:
            logger.error(f"FinancialDataTool error: {e}")
            return json.dumps({"error": str(e), "financial_data": []})

    async def _arun(self, company_name: str) -> str:
        return self._run(company_name)


class OperationalRiskTool(BaseTool):
    """Search for operational incidents, outages, and supply chain risks."""

    name: str = "operational_risk_search"
    description: str = (
        "Searches for operational risk signals: refinery outages, pipeline incidents, "
        "supply chain disruptions, logistics failures, geopolitical exposure, "
        "and infrastructure vulnerability for an oil vendor."
    )
    args_schema: Type[BaseModel] = SECFilingSearchInput

    def _run(self, company_name: str) -> str:
        try:
            results = []
            queries = [
                f"{company_name} refinery fire explosion outage shutdown 2024 2025",
                f"{company_name} pipeline leak spill incident",
                f"{company_name} supply chain disruption shortage",
                f"{company_name} geopolitical exposure sanctions country risk",
                f"{company_name} operational failure maintenance issue",
            ]
            with DDGS() as ddgs:
                for q in queries:
                    items = list(ddgs.text(q, max_results=4))
                    for item in items:
                        results.append({
                            "title": item.get("title", ""),
                            "snippet": item.get("body", "")[:400],
                            "url": item.get("href", ""),
                            "category": "operational"
                        })
            seen = set()
            unique = [r for r in results if r["url"] not in seen and not seen.add(r["url"])]
            return json.dumps({"incidents": unique[:15], "count": len(unique)})
        except Exception as e:
            logger.error(f"OperationalRiskTool error: {e}")
            return json.dumps({"error": str(e), "incidents": []})

    async def _arun(self, company_name: str) -> str:
        return self._run(company_name)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_platform(url: str) -> str:
    if "twitter.com" in url or "x.com" in url:
        return "X (Twitter)"
    if "reddit.com" in url:
        return "Reddit"
    if "linkedin.com" in url:
        return "LinkedIn"
    return "Web"


def _extract_yt_channel(text: str) -> str:
    match = re.search(r"by ([A-Za-z0-9 ]+) on YouTube", text)
    if match:
        return match.group(1).strip()
    return "Unknown Channel"


def _classify_regulatory(text: str) -> str:
    text_lower = text.lower()
    if any(w in text_lower for w in ["sec", "filing", "10-k", "8-k"]):
        return "SEC Filing"
    if any(w in text_lower for w in ["epa", "environmental"]):
        return "Environmental"
    if any(w in text_lower for w in ["osha", "workplace", "safety"]):
        return "Safety/OSHA"
    if any(w in text_lower for w in ["lawsuit", "court", "settlement"]):
        return "Legal"
    return "Regulatory"


def get_all_tools() -> list:
    """Return all tool instances for use in LangGraph agents."""
    return [
        WebSearchTool(),
        NewsSearchTool(),
        SocialMediaSearchTool(),
        YouTubeSearchTool(),
        RegulatorySearchTool(),
        FinancialDataTool(),
        OperationalRiskTool(),
    ]
