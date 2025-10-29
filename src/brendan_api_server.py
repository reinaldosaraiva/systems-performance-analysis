"""
API Server for Brendan Gregg Agent Insights

Exposes agent analysis insights via REST API for Grafana integration.
Provides endpoints compatible with Grafana's SimpleJson and JSON API data sources.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# TODO: These imports are temporarily disabled during refactoring
# Will be replaced with DDD structure in Phase 3
# try:
#     from brendan_gregg_persona import BrendanGreggInsight
#     from brendan_llm_agent import BrendanLLMAgent, LLMConfig
# except ImportError:
#     from src.brendan_gregg_persona import BrendanGreggInsight
#     from src.brendan_llm_agent import BrendanLLMAgent, LLMConfig

logger = logging.getLogger(__name__)


class GrafanaQueryRequest(BaseModel):
    """Grafana query request format."""

    target: str
    range: Optional[Dict[str, str]] = None
    interval: Optional[str] = None
    maxDataPoints: Optional[int] = None


class GrafanaSearchResponse(BaseModel):
    """Grafana search response format."""

    text: str
    value: str


class BrendanInsightsAPI:
    """API server for Brendan Gregg agent insights."""

    def __init__(
        self,
        reports_dir: Optional[Path] = None,
        prometheus_url: Optional[str] = None
    ):
        """
        Initialize the API server.

        Args:
            reports_dir: Directory containing analysis reports (uses settings if not provided)
            prometheus_url: URL of Prometheus server (uses settings if not provided)
        """
        # Load settings
        try:
            from src.infrastructure.config import get_settings
            self.settings = get_settings()
            logger.info("✅ Settings loaded from .env")
        except ImportError:
            logger.warning("⚠️ Could not load settings, using defaults")
            self.settings = None

        # Use settings or fall back to parameters/defaults
        if self.settings:
            self.reports_dir = reports_dir or self.settings.reports_dir
            self.prometheus_url = prometheus_url or self.settings.prometheus_url
        else:
            self.reports_dir = reports_dir or Path("reports")
            self.prometheus_url = prometheus_url or "http://177.93.132.48:9090"

        # Initialize repository (DDD Pattern - Phase 3)
        try:
            from src.infrastructure.persistence import FileInsightsRepository
            self.insights_repository = FileInsightsRepository(self.reports_dir)
            logger.info("✅ Repository pattern initialized")
        except ImportError as e:
            logger.warning(f"⚠️ Could not load repository: {e}")
            self.insights_repository = None

        # Initialize FastAPI with settings
        self.app = FastAPI(
            title=self.settings.api_title if self.settings else "Brendan Gregg Agent API",
            description="API for accessing Systems Performance analysis insights",
            version=self.settings.api_version if self.settings else "1.0.0",
        )

        # Enable CORS for Grafana (use settings if available)
        cors_config = {
            "allow_origins": self.settings.cors_origins if self.settings else ["*"],
            "allow_credentials": self.settings.cors_allow_credentials if self.settings else True,
            "allow_methods": self.settings.cors_allow_methods if self.settings else ["*"],
            "allow_headers": self.settings.cors_allow_headers if self.settings else ["*"],
        }
        self.app.add_middleware(CORSMiddleware, **cors_config)

        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes."""

        # Include dashboard routes from new structure
        try:
            from src.presentation.api.routes.dashboard import router as dashboard_router
            self.app.include_router(dashboard_router)
            logger.info("✅ New template-based dashboard routes loaded")
        except ImportError as e:
            logger.warning(f"⚠️ Could not load new dashboard routes: {e}")

        # Include clean insights routes (DDD - Phase 4)
        try:
            from src.presentation.api.routes import insights as insights_module
            # Inject repository into the module before including router
            if self.insights_repository:
                insights_module._repository_instance = self.insights_repository
            self.app.include_router(insights_module.router)
            logger.info("✅ Clean DDD insights routes loaded")
        except ImportError as e:
            logger.warning(f"⚠️ Could not load insights routes: {e}")

        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "service": "Brendan Gregg Agent API",
                "version": "1.0.0",
                "status": "running",
                "endpoints": {
                    "health": "/health",
                    "insights": "/api/insights",
                    "latest": "/api/insights/latest",
                    "severity": "/api/insights/severity/{severity}",
                    "component": "/api/insights/component/{component}",
                    "dashboard": "/dashboard",
                    "llm_dashboard": "/dashboard/llm",
                    "llm_insights": "/api/insights/llm",
                    "grafana_search": "/search",
                    "grafana_query": "/query",
                },
            }

        @self.app.get("/dashboard")
        async def dashboard_page():
            """Serve dashboard HTML page for embedding in Grafana."""
            html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Brendan Gregg Agent Analysis</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0b0c0e;
            color: #d8d9da;
            padding: 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: linear-gradient(135deg, #1f1f1f 0%, #2a2a2a 100%);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #333;
        }
        .stat-value {
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .stat-label {
            font-size: 14px;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .insights-table {
            background: #1a1a1a;
            border-radius: 8px;
            padding: 20px;
            border: 1px solid #333;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            text-align: left;
            padding: 12px;
            border-bottom: 2px solid #333;
            color: #999;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #222;
        }
        .severity-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
            text-transform: uppercase;
        }
        .critical { background: #dc143c; color: white; }
        .high { background: #ff8c00; color: white; }
        .medium { background: #ffd700; color: #000; }
        .low { background: #90ee90; color: #000; }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .error {
            background: #dc143c;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        h2 {
            margin-bottom: 20px;
            color: #fff;
        }
    </style>
</head>
<body>
    <div class="stats-grid">
        <div class="stat-card" style="border-left: 4px solid #1f77b4;">
            <div class="stat-value" id="total-insights">-</div>
            <div class="stat-label">Total Insights</div>
        </div>
        <div class="stat-card" style="border-left: 4px solid #dc143c;">
            <div class="stat-value" id="critical-count">-</div>
            <div class="stat-label">Critical Issues</div>
        </div>
        <div class="stat-card" style="border-left: 4px solid #ff8c00;">
            <div class="stat-value" id="high-count">-</div>
            <div class="stat-label">High Severity</div>
        </div>
        <div class="stat-card" style="border-left: 4px solid #228b22;">
            <div class="stat-value" id="api-status">✓</div>
            <div class="stat-label">API Status</div>
        </div>
    </div>

    <div class="insights-table">
        <h2>🔍 Latest Insights</h2>
        <div id="table-content" class="loading">Loading analysis...</div>
    </div>

    <script>
    async function loadAnalysis() {
        try {
            // Load summary
            const summaryResp = await fetch('/api/insights/summary');
            const summary = await summaryResp.json();

            document.getElementById('total-insights').textContent = summary.total_insights || 0;
            document.getElementById('critical-count').textContent = summary.by_severity.CRITICAL || 0;
            document.getElementById('high-count').textContent = summary.by_severity.HIGH || 0;

            // Load insights
            const insightsResp = await fetch('/api/insights?limit=10');
            const insightsData = await insightsResp.json();

            if (insightsData.insights && insightsData.insights.length > 0) {
                let tableHTML = '<table><thead><tr>';
                tableHTML += '<th>Severity</th>';
                tableHTML += '<th>Component</th>';
                tableHTML += '<th>Issue</th>';
                tableHTML += '<th>Analysis</th>';
                tableHTML += '</tr></thead><tbody>';

                insightsData.insights.forEach(insight => {
                    const severityClass = (insight.severity || 'low').toLowerCase();

                    tableHTML += '<tr>';
                    tableHTML += `<td><span class="severity-badge ${severityClass}">${insight.severity || 'UNKNOWN'}</span></td>`;
                    tableHTML += `<td>${insight.component || 'N/A'}</td>`;
                    tableHTML += `<td><strong>${insight.title || 'No title'}</strong></td>`;
                    tableHTML += `<td>${insight.observation || insight.root_cause || 'No details'}</td>`;
                    tableHTML += '</tr>';
                });

                tableHTML += '</tbody></table>';
                document.getElementById('table-content').innerHTML = tableHTML;
            } else {
                document.getElementById('table-content').innerHTML = '<p class="loading">No insights detected. System is healthy! ✓</p>';
            }

        } catch (error) {
            console.error('Error loading analysis:', error);
            document.getElementById('table-content').innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
        }
    }

    // Load immediately and refresh every 30 seconds
    loadAnalysis();
    setInterval(loadAnalysis, 30000);
    </script>
</body>
</html>
            """
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=html)

        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

        # NOTE: Old inline /api/insights routes have been migrated to
        # src/presentation/api/routes/insights.py (Phase 4 - DDD refactoring)
        # The new routes provide the same functionality with clean architecture:
        # - GET /api/insights
        # - GET /api/insights/latest
        # - GET /api/insights/severity/{severity}
        # - GET /api/insights/component/{component}
        # - GET /api/insights/summary
        # - GET /api/insights/critical

        @self.app.get("/api/insights/llm")
        async def get_llm_insights():
            """
            Get AI-powered performance insights using LLM.

            This endpoint uses the Ollama LLM to generate intelligent insights
            based on Brendan Gregg's methodology.

            Returns:
                JSON with AI-generated insights
            """
            try:
                # Initialize LLM client with settings
                from src.infrastructure.ai.ollama_llm_client import OllamaLLMClient
                from src.application.use_cases.performance import GetLLMInsightsUseCase

                if self.settings:
                    llm_client = OllamaLLMClient(
                        base_url=self.settings.ollama_url,
                        model=self.settings.ollama_model,
                        temperature=self.settings.ollama_temperature,
                    )
                else:
                    # Fallback configuration
                    llm_client = OllamaLLMClient(
                        base_url="http://localhost:11434/v1",
                        model="minimax-m2:cloud",
                        temperature=0.7,
                    )

                # Execute use case
                use_case = GetLLMInsightsUseCase(llm_client)
                insights = await use_case.execute()

                # Convert to dict format
                insights_data = []
                for insight in insights:
                    # Map fields to match Grafana dashboard expectations
                    recommendations = insight.recommendations or []
                    immediate_action = recommendations[0] if len(recommendations) > 0 else "Monitor system metrics closely"
                    long_term_fix = recommendations[-1] if len(recommendations) > 1 else recommendations[0] if len(recommendations) == 1 else "Establish baseline metrics and monitoring"

                    insights_data.append({
                        "title": insight.title,
                        "observation": insight.description,  # Grafana expects "observation"
                        "immediate_action": immediate_action,  # First recommendation
                        "long_term_fix": long_term_fix,  # Last recommendation
                        "component": insight.component,
                        "severity": insight.severity.value,
                        "timestamp": insight.timestamp.isoformat(),
                        "recommendations": recommendations,
                        "metrics": insight.metrics,
                        "root_cause": insight.root_cause or "AI analysis",
                        "confidence": 85.0,  # AI confidence level
                    })

                return {
                    "status": "success",
                    "message": "LLM insights generated successfully",
                    "timestamp": datetime.now().isoformat(),
                    "total": len(insights_data),
                    "insights": insights_data,
                    "model": llm_client.model,
                }

            except Exception as e:
                logger.error(f"Error generating LLM insights: {e}")
                return {
                    "status": "error",
                    "message": f"Failed to generate LLM insights: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                    "total": 0,
                    "insights": [],
                }

        @self.app.get("/dashboard/llm")
        async def llm_dashboard():
            """Serve LLM-powered insights dashboard for Grafana."""
            html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM-Powered Analysis - Brendan Gregg Agent</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0b0c0e;
            color: #d8d9da;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        .header h1 {
            color: white;
            font-size: 24px;
            margin-bottom: 5px;
        }
        .header .subtitle {
            color: rgba(255,255,255,0.8);
            font-size: 14px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: linear-gradient(135deg, #1f1f1f 0%, #2a2a2a 100%);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #333;
        }
        .stat-value {
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .stat-label {
            font-size: 12px;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .insight-card {
            background: #1a1a1a;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }
        .insight-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .insight-title {
            font-size: 18px;
            font-weight: bold;
            color: #fff;
        }
        .severity-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
            text-transform: uppercase;
        }
        .critical { background: #dc143c; color: white; }
        .high { background: #ff8c00; color: white; }
        .medium { background: #ffd700; color: #000; }
        .low { background: #90ee90; color: #000; }
        .section {
            margin-bottom: 15px;
        }
        .section-title {
            font-size: 12px;
            color: #999;
            text-transform: uppercase;
            margin-bottom: 5px;
            font-weight: 600;
        }
        .section-content {
            color: #d8d9da;
            line-height: 1.6;
        }
        .action-box {
            background: rgba(102, 126, 234, 0.1);
            border-left: 3px solid #667eea;
            padding: 12px;
            margin-top: 10px;
            border-radius: 4px;
        }
        .steps-list {
            list-style: none;
            counter-reset: step-counter;
        }
        .steps-list li {
            counter-increment: step-counter;
            padding: 8px 0;
            padding-left: 30px;
            position: relative;
        }
        .steps-list li:before {
            content: counter(step-counter);
            position: absolute;
            left: 0;
            background: #667eea;
            color: white;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: bold;
        }
        .loading {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        .spinner {
            border: 3px solid #333;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .error {
            background: #dc143c;
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 LLM-Powered Performance Analysis</h1>
        <div class="subtitle">Intelligent insights by MiniMax-M2 (230B parameters)</div>
    </div>

    <div class="stats-grid" id="stats">
        <div class="stat-card" style="border-left: 4px solid #667eea;">
            <div class="stat-value" id="total">-</div>
            <div class="stat-label">Total Insights</div>
        </div>
        <div class="stat-card" style="border-left: 4px solid #dc143c;">
            <div class="stat-value" id="critical">-</div>
            <div class="stat-label">Critical</div>
        </div>
        <div class="stat-card" style="border-left: 4px solid #ff8c00;">
            <div class="stat-value" id="high">-</div>
            <div class="stat-label">High</div>
        </div>
        <div class="stat-card" style="border-left: 4px solid #90ee90;">
            <div class="stat-value" id="status">⏳</div>
            <div class="stat-label">Status</div>
        </div>
    </div>

    <div id="content" class="loading">
        <div class="spinner"></div>
        <div>Running LLM analysis...</div>
        <div style="font-size: 12px; margin-top: 10px;">This may take 30-60 seconds</div>
    </div>

    <script>
    async function loadLLMInsights() {
        try {
            const response = await fetch('/api/insights/llm');
            const data = await response.json();

            // Update stats
            document.getElementById('total').textContent = data.total;
            document.getElementById('status').textContent = '✓';

            let critical = 0, high = 0;
            data.insights.forEach(i => {
                if (i.severity === 'CRITICAL') critical++;
                if (i.severity === 'HIGH') high++;
            });

            document.getElementById('critical').textContent = critical;
            document.getElementById('high').textContent = high;

            // Render insights
            let html = '';
            data.insights.forEach(insight => {
                const severityClass = insight.severity.toLowerCase();

                html += `
                <div class="insight-card">
                    <div class="insight-header">
                        <div class="insight-title">${insight.title}</div>
                        <span class="severity-badge ${severityClass}">${insight.severity}</span>
                    </div>

                    <div class="section">
                        <div class="section-title">📊 Observation</div>
                        <div class="section-content">${insight.observation}</div>
                    </div>

                    <div class="section">
                        <div class="section-title">🎯 Root Cause</div>
                        <div class="section-content">${insight.root_cause}</div>
                    </div>

                    <div class="action-box">
                        <div class="section-title">⚡ Immediate Action</div>
                        <div class="section-content">${insight.immediate_action}</div>
                    </div>

                    ${insight.investigation_steps && insight.investigation_steps.length > 0 ? `
                    <div class="section">
                        <div class="section-title">🔍 Investigation Steps</div>
                        <ul class="steps-list">
                            ${insight.investigation_steps.map(step => `<li>${step}</li>`).join('')}
                        </ul>
                    </div>
                    ` : ''}

                    <div class="section">
                        <div class="section-title">💡 Long-term Fix</div>
                        <div class="section-content">${insight.long_term_fix}</div>
                    </div>

                    <div style="margin-top: 10px; font-size: 11px; color: #666;">
                        Component: ${insight.component} | Confidence: ${insight.confidence.toFixed(1)}%
                    </div>
                </div>
                `;
            });

            document.getElementById('content').innerHTML = html;

        } catch (error) {
            console.error('Error loading LLM insights:', error);
            document.getElementById('content').innerHTML = `
                <div class="error">
                    ❌ Error: ${error.message}<br>
                    <small>Make sure Ollama is running with minimax-m2:cloud model</small>
                </div>
            `;
        }
    }

    // Load immediately
    loadLLMInsights();

    // Auto-refresh every 5 minutes (LLM analysis is slow)
    setInterval(loadLLMInsights, 300000);
    </script>
</body>
</html>
            """
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=html)

        # Grafana SimpleJson endpoints
        @self.app.get("/search")
        @self.app.post("/search")
        async def grafana_search():
            """Grafana search endpoint - returns available metrics."""
            return [
                {"text": "All Insights", "value": "all"},
                {"text": "Critical Insights", "value": "critical"},
                {"text": "High Severity", "value": "high"},
                {"text": "Medium Severity", "value": "medium"},
                {"text": "Low Severity", "value": "low"},
                {"text": "CPU Issues", "value": "cpu"},
                {"text": "Memory Issues", "value": "memory"},
                {"text": "Disk Issues", "value": "disk"},
                {"text": "Network Issues", "value": "network"},
            ]

        @self.app.post("/query")
        async def grafana_query(requests: List[GrafanaQueryRequest]):
            """Grafana query endpoint - returns time series data."""
            results = []

            for req in requests:
                target = req.target

                try:
                    insights = self._load_latest_insights()

                    # Filter based on target
                    if target == "all":
                        filtered = insights
                    elif target in ["critical", "high", "medium", "low"]:
                        filtered = [i for i in insights if i["severity"] == target.upper()]
                    elif target in ["cpu", "memory", "disk", "network"]:
                        filtered = [i for i in insights if i["component"] == target]
                    else:
                        filtered = insights

                    # Convert to Grafana time series format
                    datapoints = []
                    for insight in filtered:
                        timestamp_str = insight.get("timestamp", datetime.now().isoformat())
                        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        timestamp_ms = int(timestamp.timestamp() * 1000)

                        # Use confidence as the value
                        value = insight.get("confidence", 100.0)
                        datapoints.append([value, timestamp_ms])

                    results.append({"target": target, "datapoints": datapoints})

                except Exception as e:
                    logger.error(f"Error processing query for {target}: {e}")
                    results.append({"target": target, "datapoints": []})

            return results

        @self.app.get("/annotations")
        @self.app.post("/annotations")
        async def grafana_annotations():
            """Grafana annotations endpoint - returns insights as annotations."""
            try:
                insights = self._load_latest_insights()

                annotations = []
                for insight in insights:
                    timestamp_str = insight.get("timestamp", datetime.now().isoformat())
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    timestamp_ms = int(timestamp.timestamp() * 1000)

                    # Map severity to color
                    color_map = {
                        "CRITICAL": "red",
                        "HIGH": "orange",
                        "MEDIUM": "yellow",
                        "LOW": "green",
                    }

                    annotations.append({
                        "time": timestamp_ms,
                        "title": insight["title"],
                        "text": f"{insight['observation']}\n\n"
                        f"Root Cause: {insight['root_cause']}\n\n"
                        f"Action: {insight['immediate_action']}",
                        "tags": [
                            insight["severity"],
                            insight["component"],
                            insight["methodology"],
                        ],
                        "color": color_map.get(insight["severity"], "blue"),
                    })

                return annotations

            except Exception as e:
                logger.error(f"Error generating annotations: {e}")
                return []

    # NOTE: Old helper methods _insight_to_dict() and _load_latest_insights()
    # have been removed. This functionality is now handled by:
    # - FileInsightsRepository (src/infrastructure/persistence/)
    # - Use Cases (src/application/use_cases/performance/)
    # - Clean routes (src/presentation/api/routes/insights.py)

    def run(self, host: str = "0.0.0.0", port: int = 8080):
        """
        Run the API server.

        Args:
            host: Host to bind to
            port: Port to bind to
        """
        logger.info(f"Starting Brendan Insights API on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port, log_level="info")


def main():
    """Main entry point for the API server."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Brendan Gregg Agent Insights API Server"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port to bind to (default: 8080)"
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=Path("reports"),
        help="Directory containing analysis reports",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )

    args = parser.parse_args()

    # Try to load settings
    try:
        from src.infrastructure.config import get_settings
        settings = get_settings()
        logger.info("✅ Using settings from .env")

        # Use settings but allow CLI args to override
        host = args.host
        port = args.port
        log_level = args.log_level
        reports_dir = args.reports_dir
    except ImportError:
        logger.warning("⚠️ Settings module not available, using CLI args")
        settings = None
        host = args.host
        port = args.port
        log_level = args.log_level
        reports_dir = args.reports_dir

    # Configure logging (use settings if available)
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=settings.log_format if settings else "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create and run API server
    api = BrendanInsightsAPI(reports_dir=reports_dir)
    api.run(host=host, port=port)


if __name__ == "__main__":
    main()
