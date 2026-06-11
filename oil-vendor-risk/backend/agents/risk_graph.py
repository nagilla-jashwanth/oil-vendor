"""
LangGraph-based multi-agent system for Oil Vendor Risk Assessment.

Architecture:
  orchestrator_node  ──► financial_agent_node
                     ──► operational_agent_node
                     ──► compliance_agent_node
                     ──► social_agent_node
                          └─► aggregator_node ──► END

Each specialist agent has its own tool subset and system prompt.
The aggregator synthesises all findings into a final risk report.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict, Annotated
import operator

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from tools.search_tools import (
    FinancialDataTool,
    NewsSearchTool,
    OperationalRiskTool,
    RegulatorySearchTool,
    SocialMediaSearchTool,
    WebSearchTool,
    YouTubeSearchTool,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Graph State
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    """Shared state passed through all nodes in the LangGraph graph."""
    vendor_name: str
    additional_context: str

    # Collected findings from each specialist
    financial_findings: str
    operational_findings: str
    compliance_findings: str
    social_findings: str

    # Aggregated final report (JSON string)
    final_report: Optional[str]

    # Status messages for SSE streaming to frontend
    status_messages: Annotated[List[Dict[str, Any]], operator.add]

    # Internal message history for each agent (kept separate to avoid context bleed)
    financial_messages: List[BaseMessage]
    operational_messages: List[BaseMessage]
    compliance_messages: List[BaseMessage]
    social_messages: List[BaseMessage]
    aggregator_messages: List[BaseMessage]

    error: Optional[str]


# ---------------------------------------------------------------------------
# LLM factory (points to local vLLM)
# ---------------------------------------------------------------------------

def _make_llm(tools: Optional[list] = None) -> ChatOpenAI:
    """
    Creates a ChatOpenAI client that targets the local vLLM OpenAI-compatible
    endpoint.  AMD ROCm vLLM exposes the same API as OpenAI so we can reuse
    langchain-openai without any changes.
    """
    base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
    model = os.getenv("VLLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")

    llm = ChatOpenAI(
        base_url=base_url,
        api_key="EMPTY",          # vLLM doesn't need a real key
        model=model,
        temperature=0.1,
        max_tokens=2048,
    )
    if tools:
        llm = llm.bind_tools(tools)
    return llm


# ---------------------------------------------------------------------------
# Specialist prompts
# ---------------------------------------------------------------------------

FINANCIAL_SYSTEM_PROMPT = """You are a financial risk analyst specialising in oil & gas companies.
Your job is to gather and analyse financial health signals for the vendor provided.
Use your available tools to search for:
- Credit ratings, debt levels, leverage ratios
- Earnings trends, revenue trajectory, free cash flow
- Analyst downgrades, price targets
- Signs of financial distress or bankruptcy risk
- Recent capital market events

When you have gathered sufficient data, produce a JSON object with this structure:
{
  "summary": "<2-3 sentence executive summary>",
  "signals": [
    {"signal": "<finding>", "severity": <0-10>, "source": "<source name>", "url": "<url or empty>"}
  ],
  "score": <0-100 financial risk score where 100 is highest risk>
}
Be thorough. Call multiple tools if needed. Respond ONLY with the JSON when done."""

OPERATIONAL_SYSTEM_PROMPT = """You are an operational risk analyst specialising in oil & gas supply chains.
Your job is to assess operational risk for the vendor provided.
Use your available tools to find:
- Refinery incidents, fires, explosions, shutdowns
- Pipeline leaks or spills
- Supply chain disruptions
- Geopolitical exposure and sanctions risk
- Infrastructure vulnerabilities
- Key-person dependencies

When you have gathered sufficient data, produce a JSON object:
{
  "summary": "<2-3 sentence executive summary>",
  "signals": [
    {"signal": "<finding>", "severity": <0-10>, "source": "<source name>", "url": "<url or empty>"}
  ],
  "score": <0-100 operational risk score where 100 is highest risk>
}
Be thorough. Call multiple tools if needed. Respond ONLY with the JSON when done."""

COMPLIANCE_SYSTEM_PROMPT = """You are a compliance and regulatory risk analyst for the energy sector.
Your job is to assess regulatory and compliance risk for the vendor provided.
Use your available tools to find:
- SEC enforcement actions and fines
- EPA environmental violations and penalties
- OSHA safety violations
- Anti-bribery/FCPA violations
- Sanctions violations
- Ongoing litigation and class actions

When you have gathered sufficient data, produce a JSON object:
{
  "summary": "<2-3 sentence executive summary>",
  "signals": [
    {"signal": "<finding>", "severity": <0-10>, "source": "<source name>", "url": "<url or empty>"}
  ],
  "score": <0-100 compliance risk score where 100 is highest risk>
}
Be thorough. Call multiple tools if needed. Respond ONLY with the JSON when done."""

SOCIAL_SYSTEM_PROMPT = """You are a reputational and social risk analyst for the energy sector.
Your job is to assess reputational risk for the vendor provided.
Use your available tools to find:
- Social media controversies and negative sentiment
- Whistleblower reports
- Employee complaints and strikes
- Activist campaigns
- YouTube investigative journalism
- ESG controversies

When you have gathered sufficient data, produce a JSON object:
{
  "summary": "<2-3 sentence executive summary>",
  "signals": [
    {"signal": "<finding>", "severity": <0-10>, "source": "<source name>", "url": "<url or empty>"}
  ],
  "score": <0-100 reputational risk score where 100 is highest risk>
}
Be thorough. Call multiple tools if needed. Respond ONLY with the JSON when done."""

AGGREGATOR_SYSTEM_PROMPT = """You are a senior vendor risk officer at an oil procurement company.
You have received specialist risk assessments from four analyst teams.
Your job is to synthesise them into a final, actionable risk report.

Produce a JSON object with EXACTLY this structure (no markdown, no extra text):
{
  "vendor_name": "<vendor name>",
  "vendor_description": "<1-2 sentence description of the company>",
  "risk_level": "<low|medium|high|critical>",
  "risk_score": {
    "overall": <0-100>,
    "financial": <0-100>,
    "operational": <0-100>,
    "compliance": <0-100>,
    "reputational": <0-100>,
    "geopolitical": <0-100>
  },
  "signals": [
    {
      "category": "<financial|operational|compliance|reputational|geopolitical>",
      "signal": "<finding>",
      "source": "<source>",
      "severity": <0-10>,
      "url": "<url or empty>"
    }
  ],
  "mitigation_actions": [
    {
      "action": "<specific action>",
      "priority": "<immediate|short-term|long-term>",
      "category": "<financial|operational|compliance|reputational|geopolitical>",
      "rationale": "<why this action>"
    }
  ],
  "executive_summary": "<3-5 sentence summary for procurement leadership>",
  "data_sources_used": ["<source1>", "<source2>"],
  "assessment_timestamp": "<ISO timestamp>"
}

Rules:
- overall score = weighted average (financial 25%, operational 25%, compliance 25%, reputational 15%, geopolitical 10%)
- risk_level: 0-30=low, 31-55=medium, 56-75=high, 76-100=critical
- Include at least 3 mitigation actions per risk category that scored above 40
- Respond ONLY with the JSON object."""


# ---------------------------------------------------------------------------
# Agent node builders
# ---------------------------------------------------------------------------

def _build_specialist_node(
    role: str,
    system_prompt: str,
    tools: list,
    messages_key: str,
    findings_key: str,
    status_label: str,
):
    """
    Factory that returns a LangGraph node function for a specialist agent.
    The node runs a ReAct-style loop: LLM decides to call tools until it
    produces the final JSON findings.
    """
    llm = _make_llm(tools)
    tool_node = ToolNode(tools)

    async def node_fn(state: AgentState) -> Dict[str, Any]:
        vendor = state["vendor_name"]
        context = state.get("additional_context", "")

        status_updates = [
            {
                "agent": role,
                "status": "running",
                "message": f"{status_label} agent started for {vendor}",
            }
        ]

        # Initialise message history
        messages: List[BaseMessage] = state.get(messages_key, [])  # type: ignore
        if not messages:
            user_msg = f"Assess {role} risk for vendor: {vendor}."
            if context:
                user_msg += f" Additional context: {context}"
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_msg),
            ]

        # ReAct loop (max 8 iterations to stay within context)
        findings = ""
        for iteration in range(8):
            logger.info(f"[{role}] ReAct iteration {iteration+1}")
            response: AIMessage = await llm.ainvoke(messages)
            messages.append(response)

            # If the model called tools, execute them
            if response.tool_calls:
                tool_results = await tool_node.ainvoke({"messages": messages})
                # ToolNode returns a dict with updated messages list
                messages = tool_results.get("messages", messages)
                status_updates.append({
                    "agent": role,
                    "status": "running",
                    "message": f"{status_label}: executed {len(response.tool_calls)} tool(s)",
                })
            else:
                # No more tool calls — extract JSON findings
                content = response.content
                findings = _extract_json(content)
                break

        if not findings:
            findings = json.dumps({
                "summary": f"Could not complete {role} assessment.",
                "signals": [],
                "score": 50,
            })

        status_updates.append({
            "agent": role,
            "status": "done",
            "message": f"{status_label} assessment complete",
        })

        return {
            findings_key: findings,
            messages_key: messages,
            "status_messages": status_updates,
        }

    node_fn.__name__ = f"{role}_agent_node"
    return node_fn


# ---------------------------------------------------------------------------
# Aggregator node
# ---------------------------------------------------------------------------

async def aggregator_node(state: AgentState) -> Dict[str, Any]:
    """
    Combines specialist findings into a unified risk report.
    """
    vendor = state["vendor_name"]
    llm = _make_llm()  # no tools needed for aggregation

    status_updates = [
        {
            "agent": "aggregator",
            "status": "running",
            "message": "Synthesising all specialist findings...",
        }
    ]

    prompt = f"""Vendor: {vendor}

FINANCIAL RISK FINDINGS:
{state.get('financial_findings', 'Not available')}

OPERATIONAL RISK FINDINGS:
{state.get('operational_findings', 'Not available')}

COMPLIANCE RISK FINDINGS:
{state.get('compliance_findings', 'Not available')}

REPUTATIONAL / SOCIAL RISK FINDINGS:
{state.get('social_findings', 'Not available')}

Current timestamp: {datetime.utcnow().isoformat()}Z

Synthesise the above into the final risk report JSON as instructed."""

    messages = [
        SystemMessage(content=AGGREGATOR_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    response: AIMessage = await llm.ainvoke(messages)
    raw = response.content
    report_json = _extract_json(raw)

    # Validate / fallback
    if not report_json:
        report_json = json.dumps({
            "vendor_name": vendor,
            "vendor_description": "Assessment data unavailable.",
            "risk_level": "medium",
            "risk_score": {
                "overall": 50, "financial": 50, "operational": 50,
                "compliance": 50, "reputational": 50, "geopolitical": 50
            },
            "signals": [],
            "mitigation_actions": [],
            "executive_summary": "Unable to complete full assessment. Manual review required.",
            "data_sources_used": [],
            "assessment_timestamp": datetime.utcnow().isoformat() + "Z",
        })

    status_updates.append({
        "agent": "aggregator",
        "status": "done",
        "message": "Risk report generated",
        "data": {"report_preview": "complete"},
    })

    return {
        "final_report": report_json,
        "aggregator_messages": messages + [response],
        "status_messages": status_updates,
    }


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_risk_graph() -> StateGraph:
    """
    Builds and compiles the LangGraph state machine for vendor risk assessment.

    Graph topology (parallel specialist agents then aggregation):

        [financial_agent] ─┐
        [operational_agent]─┤
                            ├──► [aggregator] ──► END
        [compliance_agent] ─┤
        [social_agent] ────┘
    """
    financial_tools = [WebSearchTool(), NewsSearchTool(), FinancialDataTool()]
    operational_tools = [WebSearchTool(), NewsSearchTool(), OperationalRiskTool()]
    compliance_tools = [WebSearchTool(), NewsSearchTool(), RegulatorySearchTool()]
    social_tools = [WebSearchTool(), NewsSearchTool(), SocialMediaSearchTool(), YouTubeSearchTool()]

    financial_node = _build_specialist_node(
        role="financial",
        system_prompt=FINANCIAL_SYSTEM_PROMPT,
        tools=financial_tools,
        messages_key="financial_messages",
        findings_key="financial_findings",
        status_label="Financial risk",
    )
    operational_node = _build_specialist_node(
        role="operational",
        system_prompt=OPERATIONAL_SYSTEM_PROMPT,
        tools=operational_tools,
        messages_key="operational_messages",
        findings_key="operational_findings",
        status_label="Operational risk",
    )
    compliance_node = _build_specialist_node(
        role="compliance",
        system_prompt=COMPLIANCE_SYSTEM_PROMPT,
        tools=compliance_tools,
        messages_key="compliance_messages",
        findings_key="compliance_findings",
        status_label="Compliance risk",
    )
    social_node = _build_specialist_node(
        role="social",
        system_prompt=SOCIAL_SYSTEM_PROMPT,
        tools=social_tools,
        messages_key="social_messages",
        findings_key="social_findings",
        status_label="Social / Reputational risk",
    )

    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("financial_agent", financial_node)
    graph.add_node("operational_agent", operational_node)
    graph.add_node("compliance_agent", compliance_node)
    graph.add_node("social_agent", social_node)
    graph.add_node("aggregator", aggregator_node)

    # Entry: run all four specialists in parallel (LangGraph handles fan-out)
    graph.set_entry_point("financial_agent")

    # After each specialist finishes ─► aggregator
    # LangGraph doesn't do true fan-out automatically, so we chain them and
    # the aggregator runs after all four are populated in state.
    graph.add_edge("financial_agent", "operational_agent")
    graph.add_edge("operational_agent", "compliance_agent")
    graph.add_edge("compliance_agent", "social_agent")
    graph.add_edge("social_agent", "aggregator")
    graph.add_edge("aggregator", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> str:
    """Try to pull a JSON object out of a possibly noisy LLM response."""
    text = text.strip()
    # Try raw parse first
    try:
        json.loads(text)
        return text
    except Exception:
        pass
    # Find first { ... } block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass
    # Strip markdown fences
    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        json.loads(cleaned)
        return cleaned
    except Exception:
        pass
    return ""
