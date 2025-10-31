"""Pydantic schemas for Insight API responses."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class InsightResponse(BaseModel):
    """Response schema for a single insight."""

    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed description")
    component: str = Field(..., description="Component name (CPU, Memory, etc)")
    severity: str = Field(..., description="Severity level (CRITICAL, HIGH, MEDIUM, LOW)")
    timestamp: str = Field(..., description="ISO timestamp")
    recommendations: List[str] = Field(default_factory=list, description="List of recommendations")
    metrics: List[str] = Field(default_factory=list, description="Related metrics")
    root_cause: str = Field(..., description="Root cause analysis")
    observation: str = Field(..., description="Observation details")
    immediate_action: str = Field(..., description="Immediate action to take")
    confidence: float = Field(default=95.0, description="Confidence level (0-100)")
    methodology: str = Field(..., description="Analysis methodology")
    evidence: dict = Field(default_factory=dict, description="Supporting evidence")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "title": "CPU Saturation Detected",
                "description": "High load average detected",
                "component": "cpu",
                "severity": "HIGH",
                "timestamp": "2025-10-29T20:00:00",
                "recommendations": ["Scale horizontally", "Optimize workload"],
                "metrics": ["load_average=5.2", "cpu_count=4"],
                "root_cause": "use_method",
                "observation": "Load average exceeds CPU count",
                "immediate_action": "Review running processes",
                "confidence": 95.0,
                "methodology": "use_method",
                "evidence": {"load_average": "5.2", "cpu_count": "4"},
            }
        }


class InsightsListResponse(BaseModel):
    """Response schema for list of insights."""

    total: int = Field(..., description="Total number of insights")
    insights: List[InsightResponse] = Field(..., description="List of insights")
    timestamp: str = Field(..., description="Response timestamp")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "total": 2,
                "insights": [
                    {
                        "title": "CPU Saturation Detected",
                        "severity": "HIGH",
                        "component": "cpu",
                    }
                ],
                "timestamp": "2025-10-29T20:00:00",
            }
        }


class InsightSummaryResponse(BaseModel):
    """Response schema for insights summary."""

    total_insights: int = Field(..., description="Total number of insights")
    by_severity: dict = Field(..., description="Counts by severity level")
    by_component: dict = Field(..., description="Counts by component")
    timestamp: str = Field(..., description="Response timestamp")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "total_insights": 10,
                "by_severity": {"CRITICAL": 2, "HIGH": 3, "MEDIUM": 5},
                "by_component": {"cpu": 4, "memory": 3, "disk": 2, "network": 1},
                "timestamp": "2025-10-29T20:00:00",
            }
        }


class LatestInsightResponse(BaseModel):
    """Response schema for latest insight."""

    insight: Optional[InsightResponse] = Field(None, description="Latest insight")
    message: Optional[str] = Field(None, description="Message if no insights available")
    timestamp: str = Field(..., description="Response timestamp")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "insight": {
                    "title": "CPU Saturation Detected",
                    "severity": "HIGH",
                },
                "timestamp": "2025-10-29T20:00:00",
            }
        }


class InsightsBySeverityResponse(BaseModel):
    """Response schema for insights filtered by severity."""

    severity: str = Field(..., description="Severity level filter")
    count: int = Field(..., description="Number of insights with this severity")
    insights: List[InsightResponse] = Field(..., description="List of insights")
    timestamp: str = Field(..., description="Response timestamp")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "severity": "CRITICAL",
                "count": 2,
                "insights": [
                    {"title": "Memory exhaustion", "severity": "CRITICAL"}
                ],
                "timestamp": "2025-10-29T20:00:00",
            }
        }


class InsightsByComponentResponse(BaseModel):
    """Response schema for insights filtered by component."""

    component: str = Field(..., description="Component filter")
    count: int = Field(..., description="Number of insights for this component")
    insights: List[InsightResponse] = Field(..., description="List of insights")
    timestamp: str = Field(..., description="Response timestamp")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "component": "cpu",
                "count": 3,
                "insights": [
                    {"title": "CPU saturation", "component": "cpu"}
                ],
                "timestamp": "2025-10-29T20:00:00",
            }
        }
