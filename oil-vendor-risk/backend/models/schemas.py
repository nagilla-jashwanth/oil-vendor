"""
Pydantic schemas shared across the application.
"""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ── Request / Response ────────────────────────────────────────────────────────

class VendorRequest(BaseModel):
    vendor_name: str = Field(..., description="Name of the oil vendor to assess")
    ticker: Optional[str] = Field(None, description="Stock ticker symbol, e.g. XOM")


class RiskFinding(BaseModel):
    category: Literal["financial", "operational", "compliance", "reputational", "geopolitical"]
    severity: Literal["critical", "high", "medium", "low"]
    title: str
    detail: str
    source: Optional[str] = None


class MitigationAction(BaseModel):
    priority: Literal["immediate", "short_term", "long_term"]
    action: str
    rationale: str


class RiskAssessment(BaseModel):
    vendor_name: str
    overall_score: float = Field(..., ge=0, le=100, description="0=safest, 100=riskiest")
    risk_level: Literal["critical", "high", "medium", "low"]
    financial_score: float = Field(..., ge=0, le=100)
    operational_score: float = Field(..., ge=0, le=100)
    compliance_score: float = Field(..., ge=0, le=100)
    reputational_score: float = Field(..., ge=0, le=100)
    geopolitical_score: float = Field(..., ge=0, le=100)
    findings: list[RiskFinding]
    mitigations: list[MitigationAction]
    summary: str
    sources_consulted: list[str]


class AssessmentResponse(BaseModel):
    status: Literal["success", "error"]
    data: Optional[RiskAssessment] = None
    error: Optional[str] = None


# ── LangGraph state ───────────────────────────────────────────────────────────

class AgentState(BaseModel):
    """Mutable state passed through every node in the LangGraph."""
    vendor_name: str
    ticker: Optional[str] = None

    # raw intelligence gathered by tools
    web_snippets: list[str] = Field(default_factory=list)
    news_snippets: list[str] = Field(default_factory=list)
    social_snippets: list[str] = Field(default_factory=list)
    video_snippets: list[str] = Field(default_factory=list)
    financial_snippets: list[str] = Field(default_factory=list)

    # messages passed to/from the ReAct agent
    messages: list[dict] = Field(default_factory=list)

    # final structured output
    assessment: Optional[RiskAssessment] = None
    error: Optional[str] = None
