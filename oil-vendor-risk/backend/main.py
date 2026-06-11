"""
FastAPI backend for the Oil Vendor Risk Management system.
Exposes:
  GET  /api/vendors         – pre-defined vendor list
  POST /api/assess          – full risk assessment (returns final report)
  GET  /api/assess/stream   – SSE stream of assessment progress + final report
  GET  /health              – health check
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import AsyncGenerator

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

# Ensure parent package is importable when run directly
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()

from agents.risk_graph import AgentState, build_risk_graph
from models.schemas import (
    KNOWN_OIL_VENDORS,
    AssessmentResponse,
    VendorRequest,
    VendorRiskReport,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App init
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Oil Vendor Risk Management API",
    description="AI-powered third-party risk assessment for oil vendors",
    version="1.0.0",
)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compile graph once at startup
risk_graph = build_risk_graph()

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "vllm_url": os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1"),
        "model": os.getenv("VLLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.3"),
    }


@app.get("/api/vendors")
def get_vendors():
    """Returns the pre-loaded list of real-world oil vendors."""
    return {"vendors": KNOWN_OIL_VENDORS}


@app.post("/api/assess", response_model=AssessmentResponse)
async def assess_vendor(request: VendorRequest):
    """
    Runs the full LangGraph assessment pipeline and returns the final report.
    This is a long-running endpoint (1–3 min depending on model speed).
    For progress updates, use /api/assess/stream instead.
    """
    try:
        initial_state: AgentState = {
            "vendor_name": request.vendor_name,
            "additional_context": request.additional_context or "",
            "financial_findings": "",
            "operational_findings": "",
            "compliance_findings": "",
            "social_findings": "",
            "final_report": None,
            "status_messages": [],
            "financial_messages": [],
            "operational_messages": [],
            "compliance_messages": [],
            "social_messages": [],
            "aggregator_messages": [],
            "error": None,
        }

        final_state = await risk_graph.ainvoke(initial_state)

        if not final_state.get("final_report"):
            raise HTTPException(status_code=500, detail="Assessment produced no report")

        report_data = json.loads(final_state["final_report"])
        return AssessmentResponse(status="success", report=VendorRiskReport(**report_data))

    except Exception as exc:
        logger.exception("Assessment failed")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/assess/stream")
async def assess_vendor_stream(
    vendor_name: str = Query(..., description="Oil vendor name"),
    additional_context: str = Query(default="", description="Optional context"),
):
    """
    Server-Sent Events endpoint.  Streams agent status updates in real time
    and sends the final report as the last event.

    Event format:
      event: status   – AgentStatusUpdate JSON
      event: report   – VendorRiskReport JSON
      event: error    – error message string
    """

    async def event_generator() -> AsyncGenerator[dict, None]:
        try:
            initial_state: AgentState = {
                "vendor_name": vendor_name,
                "additional_context": additional_context,
                "financial_findings": "",
                "operational_findings": "",
                "compliance_findings": "",
                "social_findings": "",
                "final_report": None,
                "status_messages": [],
                "financial_messages": [],
                "operational_messages": [],
                "compliance_messages": [],
                "social_messages": [],
                "aggregator_messages": [],
                "error": None,
            }

            yield {
                "event": "status",
                "data": json.dumps({
                    "agent": "orchestrator",
                    "status": "started",
                    "message": f"Starting risk assessment for {vendor_name}",
                }),
            }

            # Stream through LangGraph using astream_events (v2 API)
            async for event in risk_graph.astream_events(initial_state, version="v2"):
                kind = event.get("event", "")

                # Node started
                if kind == "on_chain_start":
                    node_name = event.get("name", "")
                    if node_name and node_name not in ("LangGraph", "__start__"):
                        yield {
                            "event": "status",
                            "data": json.dumps({
                                "agent": node_name,
                                "status": "running",
                                "message": f"Node '{node_name}' started",
                            }),
                        }

                # Tool called
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "tool")
                    tool_input = event.get("data", {}).get("input", {})
                    yield {
                        "event": "status",
                        "data": json.dumps({
                            "agent": "tool",
                            "status": "running",
                            "message": f"Tool '{tool_name}' called",
                            "data": {"tool": tool_name, "input_preview": str(tool_input)[:120]},
                        }),
                    }

                # Node finished — check for final report
                elif kind == "on_chain_end":
                    node_name = event.get("name", "")
                    output = event.get("data", {}).get("output", {})

                    if isinstance(output, dict):
                        # Stream any status messages the node emitted
                        for msg in output.get("status_messages", []):
                            yield {"event": "status", "data": json.dumps(msg)}

                        # Final report ready
                        if output.get("final_report"):
                            try:
                                report_data = json.loads(output["final_report"])
                                yield {
                                    "event": "report",
                                    "data": json.dumps(report_data),
                                }
                            except Exception:
                                pass

            yield {
                "event": "status",
                "data": json.dumps({
                    "agent": "orchestrator",
                    "status": "done",
                    "message": "Assessment complete",
                }),
            }

        except Exception as exc:
            logger.exception("Stream assessment failed")
            yield {
                "event": "error",
                "data": json.dumps({"message": str(exc)}),
            }

    return EventSourceResponse(event_generator())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8080"))
    uvicorn.run("main:app", host=host, port=port, reload=False)
