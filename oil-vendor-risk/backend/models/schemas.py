"""
Shared Pydantic models for the Oil Vendor Risk Management API.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(str, Enum):
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    REPUTATIONAL = "reputational"
    GEOPOLITICAL = "geopolitical"


class VendorRequest(BaseModel):
    vendor_name: str = Field(..., description="Name of the oil vendor to assess")
    additional_context: Optional[str] = Field(None, description="Extra context about the vendor")


class RiskSignal(BaseModel):
    category: RiskCategory
    signal: str
    source: str
    severity: float = Field(..., ge=0.0, le=10.0)
    url: Optional[str] = None
    timestamp: Optional[str] = None


class MitigationAction(BaseModel):
    action: str
    priority: str  # immediate, short-term, long-term
    category: RiskCategory
    rationale: str


class RiskScore(BaseModel):
    overall: float = Field(..., ge=0.0, le=100.0)
    financial: float = Field(..., ge=0.0, le=100.0)
    operational: float = Field(..., ge=0.0, le=100.0)
    compliance: float = Field(..., ge=0.0, le=100.0)
    reputational: float = Field(..., ge=0.0, le=100.0)
    geopolitical: float = Field(..., ge=0.0, le=100.0)


class VendorRiskReport(BaseModel):
    vendor_name: str
    vendor_description: str
    risk_level: RiskLevel
    risk_score: RiskScore
    signals: List[RiskSignal]
    mitigation_actions: List[MitigationAction]
    executive_summary: str
    data_sources_used: List[str]
    assessment_timestamp: str


class AgentStatusUpdate(BaseModel):
    agent: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


class AssessmentResponse(BaseModel):
    status: str
    report: Optional[VendorRiskReport] = None
    error: Optional[str] = None


# Pre-defined real-world oil vendors for quick selection
KNOWN_OIL_VENDORS = [
    {
        "name": "Valero Energy Corporation",
        "description": "One of the largest petroleum refiners and marketers in the US",
        "ticker": "VLO",
        "country": "USA",
        "segment": "Refining & Marketing"
    },
    {
        "name": "SunCor Energy",
        "description": "Canada's largest integrated energy company",
        "ticker": "SU",
        "country": "Canada",
        "segment": "Integrated Oil & Gas"
    },
    {
        "name": "Petrobras",
        "description": "Brazilian multinational petroleum corporation",
        "ticker": "PBR",
        "country": "Brazil",
        "segment": "National Oil Company"
    },
]
