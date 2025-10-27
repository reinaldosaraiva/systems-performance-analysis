"""
Simple HTTP server for performance analysis without FastAPI middleware issues
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from aiohttp import web, ClientSession
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from collectors import SystemCollector
    from analyzers import USEAnalyzer, LatencyAnalyzer
    from reporters_simple import ReportGenerator
    from autogen_integration import (
        AutoGenIntegration,
        SystemMetrics,
    )
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

logger = logging.getLogger(__name__)

# Global components
collector = SystemCollector()
use_analyzer = USEAnalyzer()
latency_analyzer = LatencyAnalyzer()
report_generator = ReportGenerator()
autogen_integration = AutoGenIntegration()


async def handle_root(request):
    """Root endpoint."""
    return web.json_response(
        {
            "service": "Remote Performance Analysis Server",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
        }
    )


async def handle_health(request):
    """Health check endpoint."""
    return web.json_response(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "collector": "ok",
                "analyzer": "ok",
                "reporter": "ok",
                "autogen": "ok" if autogen_integration else "disabled",
            },
        }
    )


async def handle_metrics(request):
    """Get system metrics."""
    try:
        metrics = collector.collect_all()
        system_info = {"hostname": __import__("socket").gethostname()}

        return web.json_response(
            {
                "timestamp": datetime.now().isoformat(),
                "hostname": system_info.get("hostname", "unknown"),
                "cpu": metrics["cpu"],
                "memory": metrics["memory"],
                "disk": metrics["disk"],
                "network": metrics["network"],
                "processes": len(__import__("psutil").pids()),
                "load_average": metrics.get("cpu", {}).get("load_average", [0, 0, 0]),
            }
        )
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_analyze(request):
    """Analyze system performance."""
    try:
        data = await request.json()
        session_id = str(uuid.uuid4())

        # Parse request parameters
        include_latency = data.get("include_latency", False)
        include_autogen = data.get("include_autogen", True)
        response_format = data.get("format", "json")
        analysis_scope = data.get("analysis_scope", None)

        # Collect metrics
        metrics = collector.collect_all()
        system_info = {"hostname": __import__("socket").gethostname()}

        # Perform USE analysis
        use_analysis = use_analyzer.analyze_system(metrics)

        # Perform latency analysis if requested
        latency_analysis = None
        if include_latency:
            latency_data = collector.collect_latency_samples()
            latency_analysis = latency_analyzer.analyze_latency(latency_data)

        # Perform AutoGen analysis if requested
        autogen_analysis = None
        if include_autogen and autogen_integration:
            system_metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_utilization=metrics["cpu"]["utilization"],
                memory_utilization=metrics["memory"]["percent"],
                disk_utilization=metrics["disk"]["percent"],
                network_utilization=0.0,
                load_average=metrics["cpu"].get("load_average", [0, 0, 0]),
                process_count=len(__import__("psutil").pids()),
                context_switches=0,
                disk_io={},
                network_io={},
            )

            autogen_result = await autogen_integration.run_collaborative_analysis(
                metrics=system_metrics, analysis_scope=analysis_scope
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

        # Convert USEScore objects to dictionaries for easier handling
        use_analysis_dict = {}
        for component, score in use_analysis.items():
            use_analysis_dict[component] = {
                "status": score.status.value,
                "overall_score": score.overall_score,
                "utilization_score": score.utilization,
                "saturation_score": score.saturation,
                "errors_score": score.errors,
                "recommendation": score.recommendations[0]
                if score.recommendations
                else "No recommendations",
                "recommendations": score.recommendations,
            }

        # Generate recommendations
        recommendations = _generate_recommendations(use_analysis_dict, autogen_analysis)

        # Create response
        response_data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "system_metrics": {
                "timestamp": datetime.now().isoformat(),
                "hostname": system_info.get("hostname", "unknown"),
                "cpu": metrics["cpu"],
                "memory": metrics["memory"],
                "disk": metrics["disk"],
                "network": metrics["network"],
                "processes": len(__import__("psutil").pids()),
                "load_average": metrics["cpu"].get("load_average", [0, 0, 0]),
            },
            "use_analysis": use_analysis_dict,
            "latency_analysis": latency_analysis,
            "autogen_analysis": autogen_analysis,
            "recommendations": recommendations,
            "status": "completed",
        }

        # Return in requested format
        if response_format == "html":
            html_content = _generate_html_report(response_data)
            return web.Response(text=html_content, content_type="text/html")
        elif response_format == "markdown":
            markdown_content = _generate_markdown_report(response_data)
            return web.json_response({"markdown": markdown_content})
        else:
            return web.json_response(response_data)

    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        return web.json_response({"error": str(e)}, status=500)


def _generate_recommendations(
    use_analysis: Dict[str, Any], autogen_analysis: Optional[Dict[str, Any]]
) -> list:
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


def _generate_html_report(response_data: Dict[str, Any]) -> str:
    """Generate HTML report from analysis response."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔍 Performance Analysis Report</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; }}
            .metric {{ margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 Performance Analysis</h1>
            <p><strong>Host:</strong> {response_data["system_metrics"]["hostname"]}</p>
            <p><strong>Session:</strong> {response_data["session_id"]}</p>
            <p><strong>Generated:</strong> {response_data["timestamp"]}</p>
        </div>
        
        <h2>📊 System Metrics</h2>
        <div class="metric">
            <h3>CPU Utilization</h3>
            <p>{response_data["system_metrics"]["cpu"]["utilization"]:.1f}%</p>
        </div>
        <div class="metric">
            <h3>Memory Utilization</h3>
            <p>{response_data["system_metrics"]["memory"]["percent"]:.1f}%</p>
        </div>
        <div class="metric">
            <h3>Disk Utilization</h3>
            <p>{response_data["system_metrics"]["disk"]["percent"]:.1f}%</p>
        </div>
        
        <h2>📋 Recommendations</h2>
        <ul>
            {"".join(f"<li>{rec}</li>" for rec in response_data["recommendations"])}
        </ul>
    </body>
    </html>
    """


def _generate_markdown_report(response_data: Dict[str, Any]) -> str:
    """Generate Markdown report from analysis response."""
    md_content = f"""
# 🔍 Performance Analysis Report

**Host:** {response_data["system_metrics"]["hostname"]}  
**Session:** {response_data["session_id"]}  
**Generated:** {response_data["timestamp"]}

## 📊 System Metrics

| Metric | Value |
|--------|-------|
| CPU Utilization | {response_data["system_metrics"]["cpu"]["utilization"]:.1f}% |
| Memory Utilization | {response_data["system_metrics"]["memory"]["percent"]:.1f}% |
| Disk Utilization | {response_data["system_metrics"]["disk"]["percent"]:.1f}% |
| Processes | {response_data["system_metrics"]["processes"]} |

## 📋 Recommendations

"""

    for rec in response_data["recommendations"]:
        md_content += f"- {rec}\n"

    return md_content


def create_app():
    """Create and configure the aiohttp application."""
    app = web.Application()

    # Add routes
    app.router.add_get("/", handle_root)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/metrics", handle_metrics)
    app.router.add_post("/analyze", handle_analyze)

    return app


def main():
    """Main function to run the server."""
    import argparse

    parser = argparse.ArgumentParser(description="Remote Performance Analysis Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")

    args = parser.parse_args()

    print(f"🚀 Starting Remote Performance Analysis Server")
    print(f"📍 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"🌐 Server: http://{args.host}:{args.port}")

    app = create_app()
    web.run_app(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
