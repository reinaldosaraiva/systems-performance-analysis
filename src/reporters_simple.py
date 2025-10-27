"""
Simplified Report Generation Module

Lightweight version without matplotlib dependencies for server deployment.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from analyzers import USEScore, Status

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Simplified gerador de relatórios de performance sem gráficos."""

    def __init__(self, template_dir: Optional[Path] = None):
        """Inicializa o gerador de relatórios."""
        self.template_dir = (
            template_dir or Path(__file__).parent.parent / "reports" / "templates"
        )

    def generate_html_report(
        self,
        use_scores: Dict[str, USEScore],
        latency_analysis: Optional[Dict[str, Any]] = None,
        recommendations: Optional[List[str]] = None,
        system_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Gera relatório HTML simplificado."""

        # Generate HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🔍 Performance Analysis Report</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f4f4f4; padding: 20px; border-radius: 5px; }}
                .metric {{ margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 5px; }}
                .warning {{ background: #fff3cd; }}
                .critical {{ background: #f8d7da; }}
                .healthy {{ background: #d4edda; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔍 Performance Analysis Report</h1>
                <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
            
            <h2>📊 USE Analysis Results</h2>
        """

        for component, score in use_scores.items():
            status_class = score.status.value.lower()
            html_content += f"""
            <div class="metric {status_class}">
                <h3>{component.title()}</h3>
                <p>Status: {score.status.value}</p>
                <p>Score: {score.overall_score:.1f}%</p>
                <p>Utilization: {score.utilization_score:.1f}%</p>
                <p>Saturation: {score.saturation_score:.1f}%</p>
                <p>Errors: {score.errors_score:.1f}%</p>
            </div>
            """

        if recommendations:
            html_content += "<h2>📋 Recommendations</h2><ul>"
            for rec in recommendations:
                html_content += f"<li>{rec}</li>"
            html_content += "</ul>"

        html_content += """
        </body>
        </html>
        """

        return html_content

    def generate_markdown_report(
        self,
        use_scores: Dict[str, USEScore],
        latency_analysis: Optional[Dict[str, Any]] = None,
        recommendations: Optional[List[str]] = None,
        system_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Gera relatório Markdown simplificado."""

        md_content = f"""
# 🔍 Performance Analysis Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📊 USE Analysis Results

"""

        for component, score in use_scores.items():
            md_content += f"""
### {component.title()}

- **Status:** {score.status.value}
- **Score:** {score.overall_score:.1f}%
- **Utilization:** {score.utilization_score:.1f}%
- **Saturation:** {score.saturation_score:.1f}%
- **Errors:** {score.errors_score:.1f}%

"""

        if recommendations:
            md_content += "## 📋 Recommendations\n\n"
            for rec in recommendations:
                md_content += f"- {rec}\n"

        return md_content

    def generate_json_report(
        self,
        use_scores: Dict[str, USEScore],
        latency_analysis: Optional[Dict[str, Any]] = None,
        recommendations: Optional[List[str]] = None,
        system_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Gera relatório JSON."""
        return {
            "timestamp": datetime.now().isoformat(),
            "use_scores": {
                component: {
                    "status": score.status.value,
                    "overall_score": score.overall_score,
                    "utilization_score": score.utilization_score,
                    "saturation_score": score.saturation_score,
                    "errors_score": score.errors_score,
                    "findings": score.findings,
                }
                for component, score in use_scores.items()
            },
            "latency_analysis": latency_analysis,
            "recommendations": recommendations or [],
            "system_info": system_info or {},
        }

    def save_report(
        self,
        content: str,
        filename: str,
        format_type: str = "html",
    ) -> Path:
        """Salva relatório em arquivo."""
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}.{format_type}"
        filepath = reports_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Report saved to {filepath}")
        return filepath
