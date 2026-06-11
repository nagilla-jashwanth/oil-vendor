"""
Vendor Risk LangGraph Pipeline
================================
Graph topology (sequential with a ReAct intelligence node):

  START
    │
    ▼
 [intelligence_node]   ← ReAct agent: calls all 7 search tools in any order
    │                    until it decides it has enough data
    ▼
 [scoring_node]         ← LLM synthesises findings into category scores
    │
    ▼
 [mitigation_node]      ← LLM generates prioritised mitigation actions
    │
    ▼
  END  →  AgentState.assessment is populated
"""
from __future__ import annotations

import json
import re
import logging
from typing import Any

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent

from backend.models.schemas import (
    AgentState, RiskAssessment, RiskFinding, MitigationAction,
)
from backend.tools import ALL_TOOLS
from backend.agents.llm_factory import get_llm

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────────
# Prompts
# ────────────────────────────────────────────────────────────────────────────

INTEL_SYSTEM = """You are a senior vendor-risk intelligence analyst specialising in the global oil & gas industry.
Your task is to gather comprehensive risk intelligence about a vendor using the tools available to you.

You MUST use ALL of the following tools at least once:
- web_search
- financial_news_search
- compliance_search
- social_media_search
- video_intelligence_search
- geopolitical_risk_search
- operational_incident_search

For each tool call, craft a specific query targeting the vendor.
After gathering data, write a structured intelligence brief with sections:
FINANCIAL INTELLIGENCE, OPERATIONAL INTELLIGENCE, COMPLIANCE INTELLIGENCE,
REPUTATIONAL / SOCIAL INTELLIGENCE, GEOPOLITICAL INTELLIGENCE.
Each section should summarise the key findings and cite sources."""

SCORING_SYSTEM = """You are a quantitative risk analyst. Given an intelligence brief about an oil vendor,
you must produce a structured JSON risk assessment.

Scoring guidelines (0 = no risk, 100 = extreme risk):
- financial_score: Debt levels, credit ratings, earnings volatility, liquidity concerns
- operational_score: Supply disruptions, infrastructure failures, cyber incidents, safety record
- compliance_score: Regulatory fines, environmental violations, sanctions exposure, ESG failures
- reputational_score: Social media sentiment, controversies, boycotts, brand damage
- geopolitical_score: Country risk, OPEC+ exposure, conflict proximity, sanctions risk

overall_score = weighted average:
  financial×0.25 + operational×0.20 + compliance×0.25 + reputational×0.15 + geopolitical×0.15

risk_level thresholds:
  0–25 → "low"
  26–50 → "medium"
  51–75 → "high"
  76–100 → "critical"

Return ONLY a JSON object with this exact schema (no markdown, no extra text):
{
  "financial_score": <float>,
  "operational_score": <float>,
  "compliance_score": <float>,
  "reputational_score": <float>,
  "geopolitical_score": <float>,
  "overall_score": <float>,
  "risk_level": "<low|medium|high|critical>",
  "findings": [
    {
      "category": "<financial|operational|compliance|reputational|geopolitical>",
      "severity": "<critical|high|medium|low>",
      "title": "<short title>",
      "detail": "<2-3 sentence explanation>",
      "source": "<url or source name>"
    }
  ],
  "summary": "<3-4 sentence executive summary>",
  "sources_consulted": ["<url1>", "<url2>"]
}"""

MITIGATION_SYSTEM = """You are a strategic risk management consultant for an oil procurement organisation.
Given a vendor risk assessment JSON, generate a prioritised list of mitigation actions.

Return ONLY a JSON array (no markdown, no extra text) with this schema:
[
  {
    "priority": "<immediate|short_term|long_term>",
    "action": "<clear action statement>",
    "rationale": "<why this action addresses the identified risk>"
  }
]

Guidelines:
- immediate: actions needed within 30 days
- short_term: 1-6 months
- long_term: 6+ months strategic actions
- Provide 6-10 actions total, mix of priorities
- Make actions specific and actionable for a procurement/supply-chain team"""


# ────────────────────────────────────────────────────────────────────────────
# Helper – robust JSON extraction from LLM output
# ────────────────────────────────────────────────────────────────────────────

def _extract_json(text: str) -> Any:
    """Extract the first JSON object or array from a string."""
    # Strip markdown fences
    text = re.sub(r"```(?:json)?", "", text).strip()
    # Find the outermost { } or [ ]
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = text.find(start_char)
        if start == -1:
            continue
        depth = 0
        for i, ch in enumerate(text[start:], start=start):
            if ch == start_char:
                depth += 1
            elif ch == end_char:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
    raise ValueError(f"Could not extract JSON from: {text[:300]}")


# ────────────────────────────────────────────────────────────────────────────
# Node 1 – Intelligence gathering (ReAct agent)
# ────────────────────────────────────────────────────────────────────────────

def intelligence_node(state: dict) -> dict:
    """
    Runs a ReAct agent that iteratively calls search tools to gather
    risk intelligence about the vendor.
    """
    vendor = state["vendor_name"]
    logger.info(f"[intelligence_node] Gathering intelligence for: {vendor}")

    llm = get_llm()

    # Build the ReAct agent with all tools bound
    react_agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        state_modifier=INTEL_SYSTEM,
    )

    user_message = (
        f"Conduct a full vendor risk intelligence assessment for: {vendor}\n"
        f"Ticker symbol (if known): {state.get('ticker', 'unknown')}\n\n"
        f"Use ALL available tools to gather information on financial health, "
        f"operational incidents, compliance issues, social media sentiment, "
        f"geopolitical exposure, and video/documentary coverage."
    )

    result = react_agent.invoke({
        "messages": [HumanMessage(content=user_message)]
    })

    # Extract the final AI message as the intelligence brief
    final_messages = result.get("messages", [])
    intel_brief = ""
    for msg in reversed(final_messages):
        if isinstance(msg, AIMessage) and msg.content:
            intel_brief = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    logger.info(f"[intelligence_node] Brief length: {len(intel_brief)} chars")
    return {**state, "messages": final_messages, "web_snippets": [intel_brief]}


# ────────────────────────────────────────────────────────────────────────────
# Node 2 – Risk scoring
# ────────────────────────────────────────────────────────────────────────────

def scoring_node(state: dict) -> dict:
    """
    Takes the intelligence brief and produces structured risk scores + findings.
    """
    vendor = state["vendor_name"]
    intel_brief = (state.get("web_snippets") or ["No intelligence gathered."])[0]
    logger.info(f"[scoring_node] Scoring risk for: {vendor}")

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=SCORING_SYSTEM),
        HumanMessage(content=f"Vendor: {vendor}\n\nIntelligence Brief:\n{intel_brief}"),
    ])

    response = llm.invoke(prompt.format_messages(vendor=vendor, intel_brief=intel_brief))
    raw = response.content if isinstance(response.content, str) else str(response.content)

    try:
        scored = _extract_json(raw)
    except ValueError as exc:
        logger.error(f"[scoring_node] JSON parse error: {exc}")
        # Fallback defaults
        scored = {
            "financial_score": 50.0, "operational_score": 50.0,
            "compliance_score": 50.0, "reputational_score": 50.0,
            "geopolitical_score": 50.0, "overall_score": 50.0,
            "risk_level": "medium",
            "findings": [],
            "summary": "Unable to parse structured scoring output. Manual review recommended.",
            "sources_consulted": [],
        }

    return {**state, "financial_snippets": [json.dumps(scored)]}


# ────────────────────────────────────────────────────────────────────────────
# Node 3 – Mitigation generation
# ────────────────────────────────────────────────────────────────────────────

def mitigation_node(state: dict) -> dict:
    """
    Generates prioritised mitigation actions based on the risk scores.
    """
    vendor = state["vendor_name"]
    scored_raw = (state.get("financial_snippets") or ["{}"])[0]
    logger.info(f"[mitigation_node] Generating mitigations for: {vendor}")

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=MITIGATION_SYSTEM),
        HumanMessage(content=f"Vendor: {vendor}\n\nRisk Assessment:\n{scored_raw}"),
    ])

    response = llm.invoke(prompt.format_messages())
    raw = response.content if isinstance(response.content, str) else str(response.content)

    try:
        mitigations_raw = _extract_json(raw)
        if not isinstance(mitigations_raw, list):
            mitigations_raw = []
    except ValueError:
        mitigations_raw = []

    # ── Assemble final RiskAssessment ──────────────────────────────────────
    try:
        scored = json.loads(scored_raw)
    except Exception:
        scored = {}

    findings = []
    for f in scored.get("findings", []):
        try:
            findings.append(RiskFinding(**f))
        except Exception:
            continue

    mitigations = []
    for m in mitigations_raw:
        try:
            mitigations.append(MitigationAction(**m))
        except Exception:
            continue

    assessment = RiskAssessment(
        vendor_name=vendor,
        overall_score=float(scored.get("overall_score", 50)),
        risk_level=scored.get("risk_level", "medium"),
        financial_score=float(scored.get("financial_score", 50)),
        operational_score=float(scored.get("operational_score", 50)),
        compliance_score=float(scored.get("compliance_score", 50)),
        reputational_score=float(scored.get("reputational_score", 50)),
        geopolitical_score=float(scored.get("geopolitical_score", 50)),
        findings=findings,
        mitigations=mitigations,
        summary=scored.get("summary", "Assessment complete."),
        sources_consulted=scored.get("sources_consulted", []),
    )

    return {**state, "assessment": assessment}


# ────────────────────────────────────────────────────────────────────────────
# Build and compile the graph
# ────────────────────────────────────────────────────────────────────────────

def build_risk_graph():
    """
    Constructs and compiles the vendor risk LangGraph.
    Returns a compiled graph ready for .invoke().
    """
    builder = StateGraph(dict)

    # Register nodes
    builder.add_node("intelligence", intelligence_node)
    builder.add_node("scoring", scoring_node)
    builder.add_node("mitigation", mitigation_node)

    # Wire edges: START → intelligence → scoring → mitigation → END
    builder.add_edge(START, "intelligence")
    builder.add_edge("intelligence", "scoring")
    builder.add_edge("scoring", "mitigation")
    builder.add_edge("mitigation", END)

    return builder.compile()


# Singleton compiled graph (instantiated once at import time)
risk_graph = build_risk_graph()
