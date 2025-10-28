#!/usr/bin/env python3
"""
Remote Performance Analysis Client
Executes performance analysis on remote systems without code deployment
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import click

logger = logging.getLogger(__name__)
console = Console()


class RemoteAnalysisClient:
    """Client for remote performance analysis."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "RemotePerformanceClient/1.0",
            }
        )

    def check_server_health(self) -> bool:
        """Check if remote server is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except Exception as e:
            console.print(f"[red]❌ Server health check failed: {e}[/red]")
            return False

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics from remote server."""
        try:
            response = self.session.get(f"{self.base_url}/metrics", timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            console.print(f"[red]❌ Failed to get metrics: {e}[/red]")
            raise

    def analyze_system(
        self,
        include_latency: bool = False,
        include_autogen: bool = True,
        format: str = "json",
        analysis_scope: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Analyze system performance remotely."""

        request_data = {
            "include_latency": include_latency,
            "include_autogen": include_autogen,
            "format": format,
            "analysis_scope": analysis_scope,
        }

        try:
            response = self.session.post(
                f"{self.base_url}/analyze", json=request_data, timeout=120
            )
            response.raise_for_status()

            if format == "html":
                return {"html": response.text}
            elif format == "markdown":
                return response.json()
            else:
                return response.json()

        except Exception as e:
            console.print(f"[red]❌ Analysis failed: {e}[/red]")
            raise

    def analyze_system_async(
        self,
        include_latency: bool = False,
        include_autogen: bool = True,
        format: str = "json",
        analysis_scope: Optional[List[str]] = None,
    ) -> str:
        """Start asynchronous analysis and return task ID."""

        request_data = {
            "include_latency": include_latency,
            "include_autogen": include_autogen,
            "format": format,
            "analysis_scope": analysis_scope,
        }

        try:
            response = self.session.post(
                f"{self.base_url}/analyze/async", json=request_data, timeout=30
            )
            response.raise_for_status()
            return response.json()["task_id"]

        except Exception as e:
            console.print(f"[red]❌ Async analysis start failed: {e}[/red]")
            raise

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of asynchronous task."""
        try:
            response = self.session.get(f"{self.base_url}/task/{task_id}", timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            console.print(f"[red]❌ Failed to get task status: {e}[/red]")
            raise


class RemoteDeploymentManager:
    """Manages remote deployment of analysis server."""

    def __init__(self, host: str, user: str = "ubuntu", port: int = 22):
        self.host = host
        self.user = user
        self.port = port
        self.connection_string = f"{user}@{host}"

    def deploy_server(self, server_port: int = 8000) -> bool:
        """Deploy analysis server to remote host."""

        console.print(
            f"[blue]🚀[/blue] Deploying analysis server to {self.connection_string}"
        )

        # Create deployment script
        deployment_script = f'''
#!/bin/bash
set -e

echo "🔧 Setting up Remote Performance Analysis Server..."

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Create project directory
mkdir -p ~/remote-analysis
cd ~/remote-analysis

# Create minimal server script
cat > server.py << 'EOF'
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

import psutil
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Remote Performance Analysis Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    include_latency: bool = False
    include_autogen: bool = True
    format: str = "json"
    analysis_scope: Optional[list] = None

def collect_system_metrics() -> Dict[str, Any]:
    """Collect comprehensive system metrics."""
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        
        # Memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        # Network metrics
        network = psutil.net_io_counters()
        
        # Process metrics
        processes = len(psutil.pids())
        
        # System info
        boot_time = psutil.boot_time()
        
        return {{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu": {{
                "utilization": cpu_percent,
                "count": cpu_count,
                "load_average": list(load_avg)
            }},
            "memory": {{
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent,
                "swap_total": swap.total,
                "swap_used": swap.used,
                "swap_percent": swap.percent
            }},
            "disk": {{
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100,
                "read_bytes": disk_io.read_bytes if disk_io else 0,
                "write_bytes": disk_io.write_bytes if disk_io else 0,
                "read_count": disk_io.read_count if disk_io else 0,
                "write_count": disk_io.write_count if disk_io else 0
            }},
            "network": {{
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
                "errin": network.errin,
                "errout": network.errout,
                "dropin": network.dropin,
                "dropout": network.dropout
            }},
            "processes": processes,
            "boot_time": datetime.fromtimestamp(boot_time, timezone.utc).isoformat(),
            "uptime_hours": (datetime.now(timezone.utc).timestamp() - boot_time) / 3600
        }}
    except Exception as e:
        logger.error(f"Error collecting metrics: {{e}}")
        raise

def analyze_use_method(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze metrics using USE method."""
    analysis = {{}}
    
    # CPU Analysis
    cpu_util = metrics["cpu"]["utilization"]
    cpu_load = metrics["cpu"]["load_average"][0] if metrics["cpu"]["load_average"] else 0
    cpu_count = metrics["cpu"]["count"]
    load_per_cpu = cpu_load / cpu_count if cpu_count > 0 else 0
    
    cpu_status = "OK"
    if cpu_util > 90 or load_per_cpu > 4:
        cpu_status = "CRITICAL"
    elif cpu_util > 80 or load_per_cpu > 2:
        cpu_status = "WARNING"
    
    analysis["cpu"] = {{
        "status": cpu_status,
        "utilization": cpu_util,
        "load_per_cpu": load_per_cpu,
        "score": max(cpu_util, load_per_cpu * 25),
        "recommendation": _get_cpu_recommendation(cpu_status, cpu_util, load_per_cpu)
    }}
    
    # Memory Analysis
    mem_util = metrics["memory"]["percent"]
    mem_status = "OK"
    if mem_util > 95:
        mem_status = "CRITICAL"
    elif mem_util > 85:
        mem_status = "WARNING"
    
    analysis["memory"] = {{
        "status": mem_status,
        "utilization": mem_util,
        "score": mem_util,
        "recommendation": _get_memory_recommendation(mem_status, mem_util)
    }}
    
    # Disk Analysis
    disk_util = metrics["disk"]["percent"]
    disk_status = "OK"
    if disk_util > 95:
        disk_status = "CRITICAL"
    elif disk_util > 85:
        disk_status = "WARNING"
    
    analysis["disk"] = {{
        "status": disk_status,
        "utilization": disk_util,
        "score": disk_util,
        "recommendation": _get_disk_recommendation(disk_status, disk_util)
    }}
    
    return analysis

def _get_cpu_recommendation(status: str, util: float, load: float) -> str:
    """Get CPU recommendation based on status."""
    if status == "CRITICAL":
        return "Immediate action required: Scale horizontally or optimize CPU-intensive processes"
    elif status == "WARNING":
        return "Monitor closely: Consider optimization during peak hours"
    else:
        return "CPU utilization is within normal parameters"

def _get_memory_recommendation(status: str, util: float) -> str:
    """Get memory recommendation based on status."""
    if status == "CRITICAL":
        return "Add more RAM immediately or restart memory-intensive applications"
    elif status == "WARNING":
        return "Monitor memory trends and plan for RAM upgrade"
    else:
        return "Memory usage is within acceptable limits"

def _get_disk_recommendation(status: str, util: float) -> str:
    """Get disk recommendation based on status."""
    if status == "CRITICAL":
        return "Free up disk space immediately or expand storage"
    elif status == "WARNING":
        return "Plan disk cleanup or storage expansion soon"
    else:
        return "Disk usage is within normal parameters"

def generate_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """Generate recommendations from analysis."""
    recommendations = []
    
    for component, data in analysis.items():
        if data["status"] in ["WARNING", "CRITICAL"]:
            recommendations.append(f"{{data['recommendation']}}")
    
    # Add general recommendations
    recommendations.extend([
        "Set up automated monitoring and alerting",
        "Implement regular performance reviews",
        "Create performance baselines for comparison"
    ])
    
    return recommendations[:10]  # Limit to top 10

@app.get("/")
async def root():
    return {{
        "service": "Remote Performance Analysis Server",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }}

@app.get("/health")
async def health():
    return {{
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }}

@app.get("/metrics")
async def get_metrics():
    """Get current system metrics."""
    try:
        metrics = collect_system_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_system(request: AnalysisRequest):
    """Analyze system performance."""
    try:
        # Collect metrics
        metrics = collect_system_metrics()
        
        # Perform USE analysis
        use_analysis = analyze_use_method(metrics)
        
        # Generate recommendations
        recommendations = generate_recommendations(use_analysis)
        
        # Create response
        response = {{
            "session_id": f"session_{{int(datetime.now().timestamp())}}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_metrics": metrics,
            "use_analysis": use_analysis,
            "recommendations": recommendations,
            "status": "completed"
        }}
        
        return response
        
    except Exception as e:
        logger.error(f"Analysis error: {{e}}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting Remote Performance Analysis Server")
    print("📍 Server will be available on port {server_port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port={server_port},
        log_level="info"
    )
EOF

# Install required Python packages
echo "📦 Installing Python packages..."
export PATH="$HOME/.local/bin:$PATH"
uv init --no-readme
uv add fastapi uvicorn psutil pydantic requests

echo "✅ Server deployed successfully!"
echo "🌐 Starting server on port {server_port}..."
export PATH="$HOME/.local/bin:$PATH"
uv run python server.py
'''

        try:
            # Write deployment script to temporary file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
                f.write(deployment_script)
                script_path = f.name

            # Make script executable
            os.chmod(script_path, 0o755)

            # Execute deployment script remotely
            import subprocess

            result = subprocess.run(
                ["ssh", "-p", str(self.port), self.connection_string, f"bash -s"],
                input=open(script_path, "r").read(),
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                console.print(
                    f"[green]✅[/green] Server deployed successfully to {self.connection_string}"
                )
                console.print(
                    f"[blue]🌐[/blue] Server should be available at http://{self.host}:{server_port}"
                )
                return True
            else:
                console.print(f"[red]❌[/red] Deployment failed: {result.stderr}")
                return False

        except Exception as e:
            console.print(f"[red]❌ Deployment error: {e}[/red]")
            return False
        finally:
            # Cleanup
            try:
                os.unlink(script_path)
            except:
                pass


@click.group()
@click.option("--host", default="localhost", help="Remote server host")
@click.option("--port", type=int, default=8000, help="Remote server port")
@click.pass_context
def cli(ctx, host, port):
    """Remote Performance Analysis Client"""
    ctx.ensure_object(dict)
    ctx.obj["client"] = RemoteAnalysisClient(f"http://{host}:{port}")
    ctx.obj["host"] = host
    ctx.obj["port"] = port


@cli.command()
@click.pass_context
def health(ctx):
    """Check remote server health"""
    client = ctx.obj["client"]

    if client.check_server_health():
        console.print("[green]✅[/green] Remote server is healthy")
    else:
        console.print("[red]❌[/red] Remote server is not responding")
        sys.exit(1)


@cli.command()
@click.option("--include-latency", is_flag=True, help="Include latency analysis")
@click.option(
    "--include-autogen", is_flag=True, default=True, help="Include AutoGen analysis"
)
@click.option(
    "--format",
    type=click.Choice(["json", "html", "markdown"]),
    default="json",
    help="Output format",
)
@click.option("--output", "-o", help="Output file path")
@click.pass_context
def analyze(ctx, include_latency, include_autogen, format, output):
    """Analyze remote system performance"""
    client = ctx.obj["client"]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("🔍 Analyzing remote system...", total=None)

        try:
            result = client.analyze_system(
                include_latency=include_latency,
                include_autogen=include_autogen,
                format=format,
            )

            progress.update(task, description="✅ Analysis completed")

            # Display results
            if format == "json":
                _display_json_result(result)
            elif format == "html":
                _display_html_result(result, output)
            elif format == "markdown":
                _display_markdown_result(result, output)

        except Exception as e:
            console.print(f"[red]❌ Analysis failed: {e}[/red]")
            sys.exit(1)


@cli.command()
@click.option("--user", default="ubuntu", help="SSH user")
@click.option("--ssh-port", type=int, default=22, help="SSH port")
@click.option("--server-port", type=int, default=8000, help="Server port")
@click.argument("host")
@click.pass_context
def deploy(ctx, user, ssh_port, server_port, host):
    """Deploy analysis server to remote host"""

    manager = RemoteDeploymentManager(host, user, ssh_port)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("🚀 Deploying server...", total=None)

        success = manager.deploy_server(server_port)

        if success:
            progress.update(task, description="✅ Deployment completed")

            # Update client context for new server
            new_client = RemoteAnalysisClient(f"http://{host}:{server_port}")
            if new_client.check_server_health():
                console.print(
                    f"[green]✅[/green] Server is running at http://{host}:{server_port}"
                )
            else:
                console.print(
                    f"[yellow]⚠️[/yellow] Server deployed but health check failed"
                )
        else:
            progress.update(task, description="❌ Deployment failed")
            sys.exit(1)


def _display_json_result(result: Dict[str, Any]):
    """Display JSON analysis result."""

    # Create summary table
    table = Table(title="📊 Analysis Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Status", style="yellow")

    if "system_metrics" in result:
        metrics = result["system_metrics"]
        table.add_row(
            "CPU",
            f"{metrics['cpu']['utilization']:.1f}%",
            _get_status_color(
                result.get("use_analysis", {}).get("cpu", {}).get("status", "OK")
            ),
        )
        table.add_row(
            "Memory",
            f"{metrics['memory']['percent']:.1f}%",
            _get_status_color(
                result.get("use_analysis", {}).get("memory", {}).get("status", "OK")
            ),
        )
        table.add_row(
            "Disk",
            f"{metrics['disk']['percent']:.1f}%",
            _get_status_color(
                result.get("use_analysis", {}).get("disk", {}).get("status", "OK")
            ),
        )

    console.print(table)

    # Display recommendations
    if result.get("recommendations"):
        console.print("\n📋 Recommendations:")
        for i, rec in enumerate(result["recommendations"][:5], 1):
            console.print(f"  {i}. {rec}")


def _display_html_result(result: Dict[str, Any], output: Optional[str]):
    """Display HTML analysis result."""
    html_content = result.get("html", "")

    if output:
        with open(output, "w") as f:
            f.write(html_content)
        console.print(f"[green]✅[/green] HTML report saved to {output}")
    else:
        # Save to temporary file and open
        import tempfile
        import webbrowser
        import subprocess

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_path = f.name

        try:
            if sys.platform == "darwin":
                subprocess.run(["open", temp_path])
            elif sys.platform == "win32":
                subprocess.run(["start", temp_path], shell=True)
            else:
                subprocess.run(["xdg-open", temp_path])

            console.print(f"[green]✅[/green] HTML report opened in browser")
        except:
            console.print(
                f"[yellow]⚠️[/yellow] Could not open browser. Report saved to {temp_path}"
            )


def _display_markdown_result(result: Dict[str, Any], output: Optional[str]):
    """Display Markdown analysis result."""

    md_content = result.get("markdown", "")

    if output:
        with open(output, "w") as f:
            f.write(md_content)
        console.print(f"[green]✅[/green] Markdown report saved to {output}")
    else:
        console.print(md_content)


def _get_status_color(status: str) -> str:
    """Get colored status string."""
    colors = {
        "OK": "[green]OK[/green]",
        "WARNING": "[yellow]WARNING[/yellow]",
        "CRITICAL": "[red]CRITICAL[/red]",
    }
    return colors.get(status, "[blue]UNKNOWN[/blue]")


if __name__ == "__main__":
    cli()
