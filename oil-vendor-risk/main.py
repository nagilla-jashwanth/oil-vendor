"""
Oil Vendor Risk Management – FastAPI application
"""
from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.agents.risk_graph import risk_graph
from backend.models.schemas import AssessmentResponse, VendorRequest

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Oil Vendor Risk Management API starting…")
    yield
    logger.info("API shutting down.")


app = FastAPI(
    title="Oil Vendor Risk Management",
    description="AI-powered third-party risk assessment for oil vendors using LangGraph.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files & templates
app.mount("/static", StaticFiles(directory=BASE_DIR / "frontend" / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "frontend" / "templates"))


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok", "service": "oil-vendor-risk"}


@app.post("/api/assess", response_model=AssessmentResponse)
async def assess_vendor(body: VendorRequest):
    """
    Run the full LangGraph risk pipeline for the given vendor.
    Returns a structured RiskAssessment.
    """
    start = time.time()
    logger.info(f"Assessment requested for: {body.vendor_name}")

    try:
        initial_state = {
            "vendor_name": body.vendor_name,
            "ticker": body.ticker,
            "web_snippets": [],
            "news_snippets": [],
            "social_snippets": [],
            "video_snippets": [],
            "financial_snippets": [],
            "messages": [],
            "assessment": None,
            "error": None,
        }

        result = risk_graph.invoke(initial_state)
        assessment = result.get("assessment")

        if assessment is None:
            return AssessmentResponse(
                status="error",
                error="Graph completed but produced no assessment object.",
            )

        elapsed = round(time.time() - start, 1)
        logger.info(f"Assessment complete for {body.vendor_name} in {elapsed}s | score={assessment.overall_score}")
        return AssessmentResponse(status="success", data=assessment)

    except Exception as exc:
        logger.exception(f"Assessment failed for {body.vendor_name}: {exc}")
        return AssessmentResponse(status="error", error=str(exc))


@app.get("/api/vendors/presets")
async def vendor_presets():
    """Return the three pre-configured real-world oil vendors."""
    return {
        "vendors": [
            {
                "name": "ExxonMobil",
                "ticker": "XOM",
                "description": "World's largest publicly traded oil & gas company. HQ: Irving, TX, USA.",
                "logo_hint": "XOM",
            },
            {
                "name": "Shell plc",
                "ticker": "SHEL",
                "description": "Anglo-Dutch supermajor with global upstream, downstream & LNG operations.",
                "logo_hint": "SHEL",
            },
            {
                "name": "Rosneft",
                "ticker": "ROSN",
                "description": "Russian state-controlled oil giant; significant sanctions exposure since 2022.",
                "logo_hint": "ROSN",
            },
        ]
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 7860)),
        reload=False,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
