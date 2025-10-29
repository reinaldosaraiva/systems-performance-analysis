"""Clean API routes for performance insights (DDD architecture)."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

from src.application.use_cases.performance import (
    GetAllInsightsUseCase,
    GetLatestInsightUseCase,
    GetInsightsBySeverityUseCase,
    GetInsightsByComponentUseCase,
    GetInsightsSummaryUseCase,
    GetCriticalInsightsUseCase,
)
from src.domain.performance.entities.performance_insight import PerformanceInsight
from src.domain.performance.repositories.insights_repository import InsightsRepository
from src.presentation.api.schemas import (
    InsightsListResponse,
    InsightResponse,
    LatestInsightResponse,
    InsightsBySeverityResponse,
    InsightsByComponentResponse,
    InsightSummaryResponse,
)


router = APIRouter(prefix="/api/insights", tags=["insights"])


# Repository instance injected by brendan_api_server during setup
_repository_instance: Optional[InsightsRepository] = None


def _insight_to_response(insight: PerformanceInsight) -> InsightResponse:
    """
    Convert domain entity to API response schema.

    Args:
        insight: Performance insight entity

    Returns:
        Insight response schema
    """
    return InsightResponse(
        title=insight.title,
        description=insight.description,
        component=insight.component,
        severity=insight.severity.value,
        timestamp=insight.timestamp.isoformat(),
        recommendations=insight.recommendations,
        metrics=insight.metrics,
        root_cause=insight.root_cause or "See analysis for details",
        observation=insight.description,
        immediate_action=(
            insight.recommendations[0] if insight.recommendations
            else "Review and investigate"
        ),
        confidence=95.0,
        methodology=insight.root_cause or "use_method",
        evidence={metric: "See report" for metric in insight.metrics},
    )


def get_repository() -> InsightsRepository:
    """
    Dependency injection for repository.

    Uses the repository instance injected by brendan_api_server during setup.

    Returns:
        Insights repository instance

    Raises:
        HTTPException: If repository is not available
    """
    if _repository_instance is None:
        raise HTTPException(
            status_code=503,
            detail="Repository not configured. API may still be initializing."
        )

    return _repository_instance


@router.get("", response_model=InsightsListResponse)
async def get_all_insights(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of insights"),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    component: Optional[str] = Query(None, description="Filter by component (cpu, memory, disk, network)"),
    repository: InsightsRepository = Depends(get_repository),
):
    """
    Get all insights with optional filtering.

    This endpoint returns performance insights from the latest analysis report.
    You can filter by severity level, component, or both.

    **Query Parameters:**
    - `limit`: Maximum number of insights to return (1-1000, default: 100)
    - `severity`: Filter by severity level (CRITICAL, HIGH, MEDIUM, LOW)
    - `component`: Filter by component (cpu, memory, disk, network)

    **Example:**
    ```
    GET /api/insights?limit=10&severity=CRITICAL
    GET /api/insights?component=cpu
    GET /api/insights?severity=HIGH&component=memory&limit=5
    ```
    """
    try:
        use_case = GetAllInsightsUseCase(repository)
        insights = await use_case.execute(limit=limit, severity=severity, component=component)

        return InsightsListResponse(
            total=len(insights),
            insights=[_insight_to_response(i) for i in insights],
            timestamp=datetime.now().isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading insights: {str(e)}")


@router.get("/latest", response_model=LatestInsightResponse)
async def get_latest_insight(
    repository: InsightsRepository = Depends(get_repository),
):
    """
    Get the most recent insight.

    Returns the latest performance insight from the most recent analysis.

    **Example:**
    ```
    GET /api/insights/latest
    ```
    """
    try:
        use_case = GetLatestInsightUseCase(repository)
        insight = await use_case.execute()

        if not insight:
            return LatestInsightResponse(
                insight=None,
                message="No insights available",
                timestamp=datetime.now().isoformat(),
            )

        return LatestInsightResponse(
            insight=_insight_to_response(insight),
            message=None,
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading latest insight: {str(e)}")


@router.get("/severity/{severity}", response_model=InsightsBySeverityResponse)
async def get_insights_by_severity(
    severity: str,
    repository: InsightsRepository = Depends(get_repository),
):
    """
    Get insights filtered by severity level.

    Returns all insights with the specified severity level.

    **Path Parameters:**
    - `severity`: Severity level (CRITICAL, HIGH, MEDIUM, LOW)

    **Example:**
    ```
    GET /api/insights/severity/CRITICAL
    GET /api/insights/severity/HIGH
    ```
    """
    try:
        use_case = GetInsightsBySeverityUseCase(repository)
        insights = await use_case.execute(severity)

        return InsightsBySeverityResponse(
            severity=severity.upper(),
            count=len(insights),
            insights=[_insight_to_response(i) for i in insights],
            timestamp=datetime.now().isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading insights: {str(e)}")


@router.get("/component/{component}", response_model=InsightsByComponentResponse)
async def get_insights_by_component(
    component: str,
    repository: InsightsRepository = Depends(get_repository),
):
    """
    Get insights filtered by component.

    Returns all insights for the specified system component.

    **Path Parameters:**
    - `component`: Component name (cpu, memory, disk, network)

    **Example:**
    ```
    GET /api/insights/component/cpu
    GET /api/insights/component/memory
    ```
    """
    try:
        use_case = GetInsightsByComponentUseCase(repository)
        insights = await use_case.execute(component)

        return InsightsByComponentResponse(
            component=component.lower(),
            count=len(insights),
            insights=[_insight_to_response(i) for i in insights],
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading insights: {str(e)}")


@router.get("/summary", response_model=InsightSummaryResponse)
async def get_insights_summary(
    repository: InsightsRepository = Depends(get_repository),
):
    """
    Get summary statistics of current insights.

    Returns aggregated statistics including total count, counts by severity,
    and counts by component.

    **Example:**
    ```
    GET /api/insights/summary
    ```

    **Response:**
    ```json
    {
      "total_insights": 10,
      "by_severity": {
        "CRITICAL": 2,
        "HIGH": 3,
        "MEDIUM": 5
      },
      "by_component": {
        "cpu": 4,
        "memory": 3,
        "disk": 2,
        "network": 1
      }
    }
    ```
    """
    try:
        use_case = GetInsightsSummaryUseCase(repository)
        summary = await use_case.execute()

        return InsightSummaryResponse(
            total_insights=summary["total_insights"],
            by_severity=summary["by_severity"],
            by_component=summary["by_component"],
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


@router.get("/critical", response_model=InsightsListResponse)
async def get_critical_insights(
    repository: InsightsRepository = Depends(get_repository),
):
    """
    Get only critical severity insights.

    This is a convenience endpoint that returns only CRITICAL level insights.
    Equivalent to `/api/insights?severity=CRITICAL`.

    **Example:**
    ```
    GET /api/insights/critical
    ```
    """
    try:
        use_case = GetCriticalInsightsUseCase(repository)
        insights = await use_case.execute()

        return InsightsListResponse(
            total=len(insights),
            insights=[_insight_to_response(i) for i in insights],
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading critical insights: {str(e)}")
