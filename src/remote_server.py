"""
Remote Performance Analysis Server
FastAPI server for remote performance analysis without code deployment
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import psutil
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Add src to path for imports
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

try:
    from collectors import SystemCollector
    from analyzers import USEAnalyzer, LatencyAnalyzer
    from reporters_simple import ReportGenerator
    from autogen_integration import (
        AutoGenIntegration,
        SystemMetrics,
        PerformanceAnalysisContext,
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running this from project root directory")
    sys.exit(1)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Remote Performance Analysis Server",
    description="Server for remote performance analysis without code deployment",
    version="1.0.0",
)

# CORS middleware disabled for now - can be re-enabled later
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Global components
collector = SystemCollector()
use_analyzer = USEAnalyzer()
latency_analyzer = LatencyAnalyzer()
report_generator = ReportGenerator()
autogen_integration = AutoGenIntegration()


# Request/Response models
class AnalysisRequest(BaseModel):
    """Request model for performance analysis."""

    include_latency: bool = Field(default=False, description="Include latency analysis")
    include_autogen: bool = Field(
        default=True, description="Include AutoGen collaborative analysis"
    )
    format: str = Field(
        default="json", description="Response format (json, html, markdown)"
    )
    analysis_scope: Optional[List[str]] = Field(
        default=None, description="Specific components to analyze"
    )


class SystemMetricsResponse(BaseModel):
    """Response model for system metrics."""

    timestamp: datetime
    hostname: str
    cpu: Dict[str, Any]
    memory: Dict[str, Any]
    disk: Dict[str, Any]
    network: Dict[str, Any]
    processes: int
    load_average: List[float]


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""

    session_id: str
    timestamp: datetime
    system_metrics: SystemMetricsResponse
    use_analysis: Dict[str, Any]
    latency_analysis: Optional[Dict[str, Any]] = None
    autogen_analysis: Optional[Dict[str, Any]] = None
    recommendations: List[str]
    status: str


# Background task storage
analysis_tasks: Dict[str, Dict[str, Any]] = {}


@app.get("/")
async def root():
    """Root endpoint with server info."""
    return {
        "service": "Remote Performance Analysis Server",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "metrics": "/metrics",
            "analyze": "/analyze",
            "analyze_async": "/analyze/async",
            "task_status": "/task/{task_id}",
            "health": "/health",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "collector": "ok",
            "analyzer": "ok",
            "reporter": "ok",
            "autogen": "ok" if autogen_integration else "disabled",
        },
    }


@app.get("/metrics", response_model=SystemMetricsResponse)
async def get_system_metrics():
    """Get current system metrics."""
    try:
        # Collect metrics
        metrics = collector.collect_all()
        system_info = collector.get_system_info()

        return SystemMetricsResponse(
            timestamp=datetime.now(),
            hostname=system_info.get("hostname", "unknown"),
            cpu=metrics["cpu"],
            memory=metrics["memory"],
            disk=metrics["disk"],
            network=metrics["network"],
            processes=len(psutil.pids()),
            load_average=metrics.get("cpu", {}).get("load_average", [0, 0, 0]),
        )
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _analyze_system_internal(request: AnalysisRequest) -> AnalysisResponse:
    """Internal analysis function that always returns AnalysisResponse."""
    session_id = str(uuid.uuid4())

    # Collect metrics
    metrics = collector.collect_all()
    system_info = collector.get_system_info()

    # Perform USE analysis
    use_analysis = use_analyzer.analyze_all(metrics)

    # Perform latency analysis if requested
    latency_analysis = None
    if request.include_latency:
        latency_data = collector.collect_latency_samples()
        latency_analysis = latency_analyzer.analyze(latency_data)

    # Perform AutoGen analysis if requested
    autogen_analysis = None
    if request.include_autogen and autogen_integration:
        # Create SystemMetrics object for AutoGen
        system_metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_utilization=metrics["cpu"]["utilization"],
            memory_utilization=metrics["memory"]["percent"],
            disk_utilization=metrics["disk"]["percent"],
            network_utilization=0.0,
            load_average=metrics["cpu"].get("load_average", [0, 0, 0]),
            process_count=len(psutil.pids()),
            context_switches=0,
            disk_io={},
            network_io={},
        )

        autogen_result = await autogen_integration.run_collaborative_analysis(
            metrics=system_metrics, analysis_scope=request.analysis_scope
        )

        autogen_analysis = {
            "session_id": autogen_result.session_id,
            "consensus_score": autogen_result.consensus_score,
            "findings": [
                {
                    "id": f.id,
                    "agent": f.agent.value,
                    "component": f.component,
                    "severity": f.severity.value,
                    "title": f.title,
                    "description": f.description,
                    "recommendation": f.recommendation,
                    "confidence": f.confidence,
                    "metrics": f.metrics,
                }
                for f in autogen_result.findings
            ],
            "recommendations": autogen_result.recommendations,
            "next_steps": autogen_result.next_steps,
        }

    # Generate recommendations
    recommendations = _generate_recommendations(use_analysis, autogen_analysis)

    # Create response
    return AnalysisResponse(
        session_id=session_id,
        timestamp=datetime.now(),
        system_metrics=SystemMetricsResponse(
            timestamp=datetime.now(),
            hostname=system_info.get("hostname", "unknown"),
            cpu=metrics["cpu"],
            memory=metrics["memory"],
            disk=metrics["disk"],
            network=metrics["network"],
            processes=len(psutil.pids()),
            load_average=metrics["cpu"].get("load_average", [0, 0, 0]),
        ),
        use_analysis=use_analysis,
        latency_analysis=latency_analysis,
        autogen_analysis=autogen_analysis,
        recommendations=recommendations,
        status="completed",
    )


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_system(request: AnalysisRequest):
    """Analyze system performance."""
    try:
        # Run internal analysis
        response = await _analyze_system_internal(request)

        # Return in requested format
        if request.format == "html":
            return HTMLResponse(content=_generate_html_report(response))
        elif request.format == "markdown":
            return JSONResponse(
                content={"markdown": _generate_markdown_report(response)}
            )
        else:
            return response

    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/async")
async def analyze_system_async(
    request: AnalysisRequest, background_tasks: BackgroundTasks
):
    """Start asynchronous analysis."""
    task_id = str(uuid.uuid4())

    # Store task info
    analysis_tasks[task_id] = {
        "status": "pending",
        "created_at": datetime.now(),
        "request": request.model_dump(),
    }

    # Start background task
    background_tasks.add_task(_run_analysis_task, task_id, request)

    return {"task_id": task_id, "status": "pending", "message": "Analysis started"}


@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get status of analysis task."""
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = analysis_tasks[task_id]
    return {
        "task_id": task_id,
        "status": task["status"],
        "created_at": task["created_at"],
        "completed_at": task.get("completed_at"),
        "result": task.get("result"),
        "error": task.get("error"),
    }


def _generate_recommendations(
    use_analysis: Dict[str, Any], autogen_analysis: Optional[Dict[str, Any]]
) -> List[str]:
    """Generate recommendations from analysis results."""
    recommendations = []

    # USE Method recommendations
    for component, analysis in use_analysis.items():
        if analysis["status"] == "WARNING":
            recommendations.append(
                f"⚠️ {component.title()}: {analysis['recommendation']}"
            )
        elif analysis["status"] == "CRITICAL":
            recommendations.append(
                f"🚨 {component.title()}: {analysis['recommendation']}"
            )

    # AutoGen recommendations
    if autogen_analysis and autogen_analysis.get("recommendations"):
        recommendations.extend(autogen_analysis["recommendations"][:5])  # Top 5

    return recommendations[:10]  # Limit to top 10


def _generate_html_report(response: AnalysisResponse) -> str:
    """Generate HTML report from analysis response."""

    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔍 Remote Performance Analysis Report</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                padding: 40px; 
                text-align: center;
            }
            .header h1 { margin: 0; font-size: 2.5em; font-weight: 300; }
            .header p { margin: 10px 0; opacity: 0.9; font-size: 1.1em; }
            .content { padding: 40px; }
            .metrics { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 20px; 
                margin: 30px 0; 
            }
            .metric-card { 
                background: #f8f9fa; 
                padding: 25px; 
                border-radius: 10px; 
                text-align: center;
                border: 1px solid #e9ecef;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .metric-card:hover { 
                transform: translateY(-5px); 
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            }
            .metric-card h3 { margin: 0 0 15px 0; color: #6c757d; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; }
            .metric-card .value { font-size: 2.5em; font-weight: bold; color: #007cba; margin-bottom: 10px; }
            .metric-card .unit { color: #6c757d; font-size: 0.9em; }
            .section { margin: 30px 0; }
            .section h2 { color: #495057; margin-bottom: 20px; }
            .recommendations { background: #f8f9fa; padding: 30px; border-radius: 10px; }
            .recommendations ul { margin: 0; padding-left: 20px; }
            .recommendations li { margin: 15px 0; line-height: 1.6; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 Remote Performance Analysis</h1>
                <p><strong>Host:</strong> {hostname}</p>
                <p><strong>Session:</strong> {session_id}</p>
                <p><strong>Generated:</strong> {timestamp}</p>
            </div>
            <div class="content">
                <div class="metrics">
                    <div class="metric-card">
                        <h3>CPU Utilization</h3>
                        <div class="value">{cpu_utilization:.1f}<span class="unit">%</span></div>
                    </div>
                    <div class="metric-card">
                        <h3>Memory Utilization</h3>
                        <div class="value">{memory_utilization:.1f}<span class="unit">%</span></div>
                    </div>
                    <div class="metric-card">
                        <h3>Disk Utilization</h3>
                        <div class="value">{disk_utilization:.1f}<span class="unit">%</span></div>
                    </div>
                    <div class="metric-card">
                        <h3>Processes</h3>
                        <div class="value">{processes}</div>
                    </div>
                </div>
                
                {autogen_section}
                
                <div class="section">
                    <h2>📋 Recommendations</h2>
                    <div class="recommendations">
                        <ul>
                            {recommendations}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    # Generate AutoGen section if available
    autogen_section = ""
    if response.autogen_analysis:
        autogen_section = f"""
        <div class="section">
            <h2>🤖 AutoGen Analysis</h2>
            <p><strong>Consensus Score:</strong> {response.autogen_analysis["consensus_score"]:.1f}%</p>
            <p><strong>Findings:</strong> {len(response.autogen_analysis["findings"])}</p>
        </div>
        """

    # Generate recommendations list
    recommendations_html = "\n".join(
        f"<li>{rec}</li>" for rec in response.recommendations
    )

    return html_template.format(
        hostname=response.system_metrics.hostname,
        session_id=response.session_id,
        timestamp=response.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        cpu_utilization=response.system_metrics.cpu["utilization"],
        memory_utilization=response.system_metrics.memory["percent"],
        disk_utilization=response.system_metrics.disk["percent"],
        processes=response.system_metrics.processes,
        autogen_section=autogen_section,
        recommendations=recommendations_html,
    )


def _generate_markdown_report(response: AnalysisResponse) -> str:
    """Generate Markdown report from analysis response."""

    md_content = f"""
# 🔍 Remote Performance Analysis Report

**Host:** {response.system_metrics.hostname}  
**Session:** {response.session_id}  
**Generated:** {response.timestamp.strftime("%Y-%m-%d %H:%M:%S")}

## 📊 System Metrics

| Metric | Value |
|--------|-------|
| CPU Utilization | {response.system_metrics.cpu["utilization"]:.1f}% |
| Memory Utilization | {response.system_metrics.memory["percent"]:.1f}% |
| Disk Utilization | {response.system_metrics.disk["percent"]:.1f}% |
| Processes | {response.system_metrics.processes} |

"""

    if response.autogen_analysis:
        md_content += f"""
## 🤖 AutoGen Analysis

**Consensus Score:** {response.autogen_analysis["consensus_score"]:.1f}%  
**Findings:** {len(response.autogen_analysis["findings"])}

"""

    md_content += """
## 📋 Recommendations

"""

    for rec in response.recommendations:
        md_content += f"- {rec}\n"

    return md_content


async def _run_analysis_task(task_id: str, request: AnalysisRequest):
    """Run analysis in background."""
    try:
        # Update task status
        analysis_tasks[task_id]["status"] = "running"

        # Run analysis (internal call, always returns AnalysisResponse)
        result = await _analyze_system_internal(request)

        # Store result
        analysis_tasks[task_id]["status"] = "completed"
        analysis_tasks[task_id]["completed_at"] = datetime.now()
        analysis_tasks[task_id]["result"] = result.model_dump()

    except Exception as e:
        logger.error(f"Background analysis failed: {e}")
        analysis_tasks[task_id]["status"] = "failed"
        analysis_tasks[task_id]["completed_at"] = datetime.now()
        analysis_tasks[task_id]["error"] = str(e)


def main():
    """Main function to run the server."""
    import argparse

    parser = argparse.ArgumentParser(description="Remote Performance Analysis Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    print(f"🚀 Starting Remote Performance Analysis Server")
    print(f"📍 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"🌐 API Docs: http://{args.host}:{args.port}/docs")

    uvicorn.run(
        "remote_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
