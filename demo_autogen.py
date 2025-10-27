#!/usr/bin/env python3
"""
AutoGen Multi-Agent Performance Analysis Demo

Demonstration of collaborative performance analysis using specialized AI agents.
This standalone demo shows the architecture and workflow without requiring
the full project dependencies.
"""

import asyncio
import json
import logging
import os
import platform
import sys
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

import psutil
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

console = Console()


class AgentRole(str, Enum):
    """Roles for specialized agents."""

    PERFORMANCE_ANALYST = "performance_analyst"
    INFRASTRUCTURE_EXPERT = "infrastructure_expert"
    SECURITY_ANALYST = "security_analyst"
    COST_OPTIMIZER = "cost_optimizer"
    REPORT_GENERATOR = "report_generator"
    COORDINATOR = "coordinator"


class AnalysisSeverity(str, Enum):
    """Severity levels for analysis findings."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SystemMetrics:
    """System metrics data structure."""

    timestamp: datetime
    cpu_utilization: float
    memory_utilization: float
    disk_utilization: float
    network_utilization: float
    load_average: List[float]
    process_count: int
    context_switches: int
    disk_io: Dict[str, Any]
    network_io: Dict[str, Any]


@dataclass
class AnalysisFinding:
    """Individual analysis finding."""

    id: str
    agent: AgentRole
    component: str
    severity: AnalysisSeverity
    title: str
    description: str
    recommendation: str
    metrics: Dict[str, float]
    confidence: float
    timestamp: datetime


@dataclass
class CollaborativeAnalysis:
    """Complete collaborative analysis result."""

    session_id: str
    timestamp: datetime
    system_metrics: SystemMetrics
    findings: List[AnalysisFinding]
    consensus_score: float
    recommendations: List[str]
    next_steps: List[str]
    agent_interactions: List[Dict[str, Any]]


class MockAgent:
    """Mock agent for demonstration."""

    def __init__(self, name: str, role: AgentRole, system_message: str):
        self.name = name
        self.role = role
        self.system_message = system_message

    async def analyze(self, metrics: SystemMetrics) -> List[AnalysisFinding]:
        """Mock analysis based on role and metrics."""

        findings = []

        if self.role == AgentRole.PERFORMANCE_ANALYST:
            findings.extend(self._analyze_performance(metrics))
        elif self.role == AgentRole.INFRASTRUCTURE_EXPERT:
            findings.extend(self._analyze_infrastructure(metrics))
        elif self.role == AgentRole.SECURITY_ANALYST:
            findings.extend(self._analyze_security(metrics))
        elif self.role == AgentRole.COST_OPTIMIZER:
            findings.extend(self._analyze_cost(metrics))
        elif self.role == AgentRole.REPORT_GENERATOR:
            findings.extend(self._analyze_reporting(metrics))
        elif self.role == AgentRole.COORDINATOR:
            findings.extend(self._analyze_coordination(metrics))

        return findings

    def _analyze_performance(self, metrics: SystemMetrics) -> List[AnalysisFinding]:
        """Analyze performance using USE method."""
        findings = []

        # CPU Analysis
        if metrics.cpu_utilization > 80:
            findings.append(
                AnalysisFinding(
                    id=str(uuid.uuid4()),
                    agent=self.role,
                    component="cpu",
                    severity=AnalysisSeverity.HIGH
                    if metrics.cpu_utilization > 90
                    else AnalysisSeverity.MEDIUM,
                    title="High CPU Utilization Detected",
                    description=f"CPU utilization is at {metrics.cpu_utilization:.1f}%, which exceeds recommended thresholds.",
                    recommendation="Consider scaling horizontally or optimizing CPU-intensive processes.",
                    metrics={"cpu_utilization": metrics.cpu_utilization},
                    confidence=0.85,
                    timestamp=datetime.now(),
                )
            )

        # Memory Analysis
        if metrics.memory_utilization > 85:
            findings.append(
                AnalysisFinding(
                    id=str(uuid.uuid4()),
                    agent=self.role,
                    component="memory",
                    severity=AnalysisSeverity.HIGH
                    if metrics.memory_utilization > 95
                    else AnalysisSeverity.MEDIUM,
                    title="High Memory Utilization",
                    description=f"Memory utilization is at {metrics.memory_utilization:.1f}%, approaching saturation.",
                    recommendation="Investigate memory leaks, add more RAM, or implement memory optimization.",
                    metrics={"memory_utilization": metrics.memory_utilization},
                    confidence=0.90,
                    timestamp=datetime.now(),
                )
            )

        # Load Average Analysis
        if metrics.load_average and len(metrics.load_average) > 0:
            load_1m = metrics.load_average[0]
            cpu_count = psutil.cpu_count()
            load_per_cpu = load_1m / cpu_count if cpu_count and cpu_count > 0 else 0

            if load_per_cpu > 2.0:
                findings.append(
                    AnalysisFinding(
                        id=str(uuid.uuid4()),
                        agent=self.role,
                        component="cpu",
                        severity=AnalysisSeverity.HIGH
                        if load_per_cpu > 4.0
                        else AnalysisSeverity.MEDIUM,
                        title="High Load Average",
                        description=f"Load average ({load_1m:.2f}) is {load_per_cpu:.1f}x CPU count.",
                        recommendation="Investigate CPU bottlenecks and consider load balancing.",
                        metrics={"load_average": load_1m, "load_per_cpu": load_per_cpu},
                        confidence=0.80,
                        timestamp=datetime.now(),
                    )
                )

        return findings

    def _analyze_infrastructure(self, metrics: SystemMetrics) -> List[AnalysisFinding]:
        """Analyze infrastructure aspects."""
        findings = []

        # Disk Utilization
        if metrics.disk_utilization > 85:
            findings.append(
                AnalysisFinding(
                    id=str(uuid.uuid4()),
                    agent=self.role,
                    component="disk",
                    severity=AnalysisSeverity.HIGH
                    if metrics.disk_utilization > 95
                    else AnalysisSeverity.MEDIUM,
                    title="Disk Space Running Low",
                    description=f"Disk utilization is at {metrics.disk_utilization:.1f}%. Free up space soon.",
                    recommendation="Clean up unnecessary files, archive old data, or expand storage.",
                    metrics={"disk_utilization": metrics.disk_utilization},
                    confidence=0.95,
                    timestamp=datetime.now(),
                )
            )

        # Process Count
        if metrics.process_count > 500:
            findings.append(
                AnalysisFinding(
                    id=str(uuid.uuid4()),
                    agent=self.role,
                    component="processes",
                    severity=AnalysisSeverity.MEDIUM,
                    title="High Process Count",
                    description=f"System has {metrics.process_count} running processes, which may impact performance.",
                    recommendation="Review running processes and terminate unnecessary ones.",
                    metrics={"process_count": metrics.process_count},
                    confidence=0.70,
                    timestamp=datetime.now(),
                )
            )

        return findings

    def _analyze_security(self, metrics: SystemMetrics) -> List[AnalysisFinding]:
        """Analyze security aspects."""
        findings = []

        # High resource usage could indicate security issues
        if metrics.cpu_utilization > 95 or metrics.memory_utilization > 95:
            findings.append(
                AnalysisFinding(
                    id=str(uuid.uuid4()),
                    agent=self.role,
                    component="security",
                    severity=AnalysisSeverity.MEDIUM,
                    title="Unusual Resource Consumption",
                    description="Extremely high resource usage may indicate security issues like crypto-mining or DDoS.",
                    recommendation="Investigate processes causing high resource usage and check for security breaches.",
                    metrics={
                        "cpu_utilization": metrics.cpu_utilization,
                        "memory_utilization": metrics.memory_utilization,
                    },
                    confidence=0.60,
                    timestamp=datetime.now(),
                )
            )

        return findings

    def _analyze_cost(self, metrics: SystemMetrics) -> List[AnalysisFinding]:
        """Analyze cost optimization opportunities."""
        findings = []

        # Underutilized resources
        if metrics.cpu_utilization < 20:
            findings.append(
                AnalysisFinding(
                    id=str(uuid.uuid4()),
                    agent=self.role,
                    component="cost",
                    severity=AnalysisSeverity.LOW,
                    title="Underutilized CPU Resources",
                    description=f"CPU utilization is only {metrics.cpu_utilization:.1f}%, indicating potential over-provisioning.",
                    recommendation="Consider downsizing instances or consolidating workloads to reduce costs.",
                    metrics={"cpu_utilization": metrics.cpu_utilization},
                    confidence=0.75,
                    timestamp=datetime.now(),
                )
            )

        if metrics.memory_utilization < 30:
            findings.append(
                AnalysisFinding(
                    id=str(uuid.uuid4()),
                    agent=self.role,
                    component="cost",
                    severity=AnalysisSeverity.LOW,
                    title="Underutilized Memory Resources",
                    description=f"Memory utilization is only {metrics.memory_utilization:.1f}%, suggesting over-allocation.",
                    recommendation="Right-size memory allocation or use smaller instance types.",
                    metrics={"memory_utilization": metrics.memory_utilization},
                    confidence=0.70,
                    timestamp=datetime.now(),
                )
            )

        return findings

    def _analyze_reporting(self, metrics: SystemMetrics) -> List[AnalysisFinding]:
        """Analyze reporting and monitoring aspects."""
        findings = []

        # General monitoring recommendation
        findings.append(
            AnalysisFinding(
                id=str(uuid.uuid4()),
                agent=self.role,
                component="monitoring",
                severity=AnalysisSeverity.INFO,
                title="Monitoring Enhancement Recommended",
                description="Implement comprehensive monitoring for better visibility into system performance.",
                recommendation="Set up dashboards, alerts, and regular performance reports.",
                metrics={},
                confidence=0.80,
                timestamp=datetime.now(),
            )
        )

        return findings

    def _analyze_coordination(self, metrics: SystemMetrics) -> List[AnalysisFinding]:
        """Analyze coordination aspects."""
        findings = []

        # Overall system health
        overall_score = (
            100
            - metrics.cpu_utilization
            + 100
            - metrics.memory_utilization
            + 100
            - metrics.disk_utilization
        ) / 3

        if overall_score < 30:
            severity = AnalysisSeverity.CRITICAL
        elif overall_score < 50:
            severity = AnalysisSeverity.HIGH
        elif overall_score < 70:
            severity = AnalysisSeverity.MEDIUM
        else:
            severity = AnalysisSeverity.LOW

        findings.append(
            AnalysisFinding(
                id=str(uuid.uuid4()),
                agent=self.role,
                component="system",
                severity=severity,
                title=f"System Health Score: {overall_score:.1f}%",
                description=f"Overall system health based on resource utilization metrics.",
                recommendation="Address high-priority issues first to improve system health.",
                metrics={"health_score": overall_score},
                confidence=0.85,
                timestamp=datetime.now(),
            )
        )

        return findings


class AutoGenDemo:
    """AutoGen demonstration orchestrator."""

    def __init__(self):
        """Initialize the demo orchestrator."""
        self.agents = self._setup_agents()
        console.print("[green]✅[/green] AutoGen Demo initialized")

    def _setup_agents(self) -> Dict[AgentRole, MockAgent]:
        """Setup mock agents with specialized roles."""

        agents = {
            AgentRole.PERFORMANCE_ANALYST: MockAgent(
                name="PerformanceAnalyst",
                role=AgentRole.PERFORMANCE_ANALYST,
                system_message="Senior Performance Analyst specializing in USE Method and system optimization.",
            ),
            AgentRole.INFRASTRUCTURE_EXPERT: MockAgent(
                name="InfrastructureExpert",
                role=AgentRole.INFRASTRUCTURE_EXPERT,
                system_message="Infrastructure Expert specializing in system architecture and optimization.",
            ),
            AgentRole.SECURITY_ANALYST: MockAgent(
                name="SecurityAnalyst",
                role=AgentRole.SECURITY_ANALYST,
                system_message="Security Analyst specializing in performance-security trade-offs.",
            ),
            AgentRole.COST_OPTIMIZER: MockAgent(
                name="CostOptimizer",
                role=AgentRole.COST_OPTIMIZER,
                system_message="Cost Optimization Expert specializing in resource efficiency.",
            ),
            AgentRole.REPORT_GENERATOR: MockAgent(
                name="ReportGenerator",
                role=AgentRole.REPORT_GENERATOR,
                system_message="Technical Communication Expert specializing in performance reporting.",
            ),
            AgentRole.COORDINATOR: MockAgent(
                name="Coordinator",
                role=AgentRole.COORDINATOR,
                system_message="Performance Analysis Coordinator for orchestrating collaborative analysis.",
            ),
        }

        return agents

    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""

        console.print("[blue]📊[/blue] Collecting system metrics...")

        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        network = psutil.net_io_counters()

        try:
            load_avg = psutil.getloadavg()
        except (AttributeError, OSError):
            # Windows doesn't have getloadavg
            load_avg = [0.0, 0.0, 0.0]

        system_metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_utilization=cpu_percent,
            memory_utilization=memory.percent,
            disk_utilization=(disk.used / disk.total) * 100,
            network_utilization=0.0,
            load_average=list(load_avg),
            process_count=len(psutil.pids()),
            context_switches=0,
            disk_io={
                "read_bytes": disk.used,
                "write_bytes": 0,
            },
            network_io={
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
            },
        )

        console.print("[green]✅[/green] System metrics collected")
        return system_metrics

    async def run_collaborative_analysis(self) -> CollaborativeAnalysis:
        """Run collaborative performance analysis with all agents."""

        session_id = str(uuid.uuid4())
        console.print(
            f"[blue]🚀[/blue] Starting collaborative analysis (Session: {session_id[:8]})"
        )

        # Collect metrics
        metrics = await self.collect_system_metrics()

        # Run analysis with all agents
        all_findings = []
        agent_interactions = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for role, agent in self.agents.items():
                task = progress.add_task(
                    f"🤖 Running {agent.name} analysis...", total=None
                )

                # Simulate agent interaction
                interaction = {
                    "agent": agent.name,
                    "role": role.value,
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Starting {role.value} analysis...",
                }
                agent_interactions.append(interaction)

                # Get findings from agent
                findings = await agent.analyze(metrics)
                all_findings.extend(findings)

                # Record completion
                interaction = {
                    "agent": agent.name,
                    "role": role.value,
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Completed {role.value} analysis with {len(findings)} findings.",
                }
                agent_interactions.append(interaction)

                progress.update(
                    task,
                    description=f"✅ {agent.name} completed ({len(findings)} findings)",
                )

        # Generate recommendations
        recommendations = self._generate_recommendations(all_findings)

        # Calculate consensus score
        consensus_score = self._calculate_consensus_score(all_findings)

        # Generate next steps
        next_steps = self._generate_next_steps(all_findings)

        collaborative_analysis = CollaborativeAnalysis(
            session_id=session_id,
            timestamp=datetime.now(),
            system_metrics=metrics,
            findings=all_findings,
            consensus_score=consensus_score,
            recommendations=recommendations,
            next_steps=next_steps,
            agent_interactions=agent_interactions,
        )

        console.print(
            f"[green]✅[/green] Collaborative analysis completed (Consensus: {consensus_score:.1f}%)"
        )
        return collaborative_analysis

    def _generate_recommendations(self, findings: List[AnalysisFinding]) -> List[str]:
        """Generate recommendations from findings."""

        recommendations = []

        # Group by severity
        critical_findings = [
            f for f in findings if f.severity == AnalysisSeverity.CRITICAL
        ]
        high_findings = [f for f in findings if f.severity == AnalysisSeverity.HIGH]

        # Critical recommendations
        if critical_findings:
            recommendations.append(
                "🚨 IMMEDIATE ACTION REQUIRED: Address critical performance issues"
            )
            for finding in critical_findings[:3]:  # Top 3 critical
                recommendations.append(f"• {finding.recommendation}")

        # High priority recommendations
        if high_findings:
            recommendations.append("⚠️ HIGH PRIORITY: Address these issues soon")
            for finding in high_findings[:3]:  # Top 3 high
                recommendations.append(f"• {finding.recommendation}")

        # General recommendations
        recommendations.extend(
            [
                "📊 Set up automated monitoring and alerting",
                "🔧 Implement regular performance reviews",
                "📈 Create performance baselines and trends",
                "🛡️ Review security configurations regularly",
                "💰 Conduct monthly cost optimization reviews",
            ]
        )

        return recommendations[:10]  # Limit to top 10

    def _calculate_consensus_score(self, findings: List[AnalysisFinding]) -> float:
        """Calculate consensus score among agents."""

        if not findings:
            return 0.0

        # Calculate based on confidence and agent diversity
        total_confidence = sum(finding.confidence for finding in findings)
        avg_confidence = total_confidence / len(findings)

        # Agent diversity bonus
        agent_roles = set(finding.agent for finding in findings)
        diversity_bonus = min(len(agent_roles) / len(self.agents), 1.0) * 15

        # Severity consideration
        severity_weights = {
            AnalysisSeverity.CRITICAL: 1.5,
            AnalysisSeverity.HIGH: 1.2,
            AnalysisSeverity.MEDIUM: 1.0,
            AnalysisSeverity.LOW: 0.8,
            AnalysisSeverity.INFO: 0.5,
        }

        severity_bonus = (
            sum(severity_weights.get(f.severity, 1.0) for f in findings)
            / len(findings)
            * 10
        )

        consensus_score = min(avg_confidence + diversity_bonus + severity_bonus, 100.0)
        return consensus_score

    def _generate_next_steps(self, findings: List[AnalysisFinding]) -> List[str]:
        """Generate next steps based on findings."""

        next_steps = []

        # Priority-based next steps
        critical_count = len(
            [f for f in findings if f.severity == AnalysisSeverity.CRITICAL]
        )
        high_count = len([f for f in findings if f.severity == AnalysisSeverity.HIGH])

        if critical_count > 0:
            next_steps.append(
                f"Address {critical_count} critical issues within 24 hours"
            )

        if high_count > 0:
            next_steps.append(
                f"Plan remediation for {high_count} high-priority issues within 1 week"
            )

        next_steps.extend(
            [
                "Implement automated monitoring dashboards",
                "Schedule follow-up performance analysis in 24 hours",
                "Create implementation roadmap for all recommendations",
                "Document performance baselines for future comparison",
                "Review and update SLA requirements based on findings",
            ]
        )

        return next_steps

    def generate_report(
        self, analysis: CollaborativeAnalysis, format: str = "html"
    ) -> Path:
        """Generate report from collaborative analysis."""

        console.print("[blue]📝[/blue] Generating comprehensive report...")

        # Create report data
        report_data = {
            "session_id": analysis.session_id,
            "timestamp": analysis.timestamp.isoformat(),
            "system_metrics": asdict(analysis.system_metrics),
            "findings": [asdict(f) for f in analysis.findings],
            "consensus_score": analysis.consensus_score,
            "recommendations": analysis.recommendations,
            "next_steps": analysis.next_steps,
        }

        # Generate report content
        if format.lower() == "html":
            report_content = self._generate_html_report(report_data)
            extension = "html"
        elif format.lower() == "markdown":
            report_content = self._generate_markdown_report(report_data)
            extension = "md"
        elif format.lower() == "json":
            report_content = json.dumps(report_data, indent=2, default=str)
            extension = "json"
        else:
            raise ValueError(f"Unsupported format: {format}")

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"autogen_demo_analysis_{timestamp}.{extension}"
        report_path = Path("reports") / filename
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        console.print(f"[green]✅[/green] Report saved to: {report_path}")
        return report_path

    def _generate_html_report(self, data: Dict[str, Any]) -> str:
        """Generate HTML report from analysis data."""

        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>🤖 AutoGen Performance Analysis Demo</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f7fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border-left: 4px solid #007cba; }}
        .finding {{ margin: 20px 0; padding: 20px; border-radius: 10px; border-left: 4px solid; }}
        .critical {{ border-left-color: #d32f2f; background: #ffebee; }}
        .high {{ border-left-color: #f57c00; background: #fff3e0; }}
        .medium {{ border-left-color: #fbc02d; background: #fffde7; }}
        .low {{ border-left-color: #388e3c; background: #e8f5e8; }}
        .info {{ border-left-color: #1976d2; background: #e3f2fd; }}
        .consensus {{ font-size: 2em; font-weight: bold; color: #007cba; text-align: center; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AutoGen Performance Analysis Demo</h1>
            <p><strong>Session:</strong> {data["session_id"]}</p>
            <p><strong>Generated:</strong> {data["timestamp"]}</p>
            <div class="consensus">{data["consensus_score"]:.1f}% Consensus</div>
        </div>

        <h2>📊 System Metrics</h2>
        <div class="metrics">
            <div class="metric-card">
                <h3>CPU Utilization</h3>
                <div style="font-size: 2em; color: #007cba;">{
            data["system_metrics"]["cpu_utilization"]:.1f}%</div>
            </div>
            <div class="metric-card">
                <h3>Memory Utilization</h3>
                <div style="font-size: 2em; color: #007cba;">{
            data["system_metrics"]["memory_utilization"]:.1f}%</div>
            </div>
            <div class="metric-card">
                <h3>Disk Utilization</h3>
                <div style="font-size: 2em; color: #007cba;">{
            data["system_metrics"]["disk_utilization"]:.1f}%</div>
            </div>
            <div class="metric-card">
                <h3>Process Count</h3>
                <div style="font-size: 2em; color: #007cba;">{
            data["system_metrics"]["process_count"]
        }</div>
            </div>
        </div>

        <h2>🔍 Key Findings</h2>
        {
            "".join(
                [
                    f'''
        <div class="finding {finding["severity"]}">
            <h4>{finding["title"]}</h4>
            <p><strong>Agent:</strong> {finding["agent"].replace("_", " ").title()}</p>
            <p><strong>Severity:</strong> {finding["severity"].upper()}</p>
            <p><strong>Confidence:</strong> {finding["confidence"]:.1f}%</p>
            <p>{finding["description"]}</p>
            <p><strong>Recommendation:</strong> {finding["recommendation"]}</p>
        </div>
        '''
                    for finding in data["findings"]
                ]
            )
        }

        <h2>📋 Recommendations</h2>
        <ul>
            {"".join([f"<li>{rec}</li>" for rec in data["recommendations"]])}
        </ul>

        <h2>🚀 Next Steps</h2>
        <ol>
            {"".join([f"<li>{step}</li>" for step in data["next_steps"]])}
        </ol>
    </div>
</body>
</html>
        """

    def _generate_markdown_report(self, data: Dict[str, Any]) -> str:
        """Generate Markdown report from analysis data."""

        md_content = f"""
# 🤖 AutoGen Performance Analysis Demo

**Session ID:** {data["session_id"]}  
**Generated:** {data["timestamp"]}  
**Consensus Score:** {data["consensus_score"]:.1f}%

## 📊 System Metrics

| Metric | Value |
|--------|-------|
| CPU Utilization | {data["system_metrics"]["cpu_utilization"]:.1f}% |
| Memory Utilization | {data["system_metrics"]["memory_utilization"]:.1f}% |
| Disk Utilization | {data["system_metrics"]["disk_utilization"]:.1f}% |
| Process Count | {data["system_metrics"]["process_count"]} |

## 🔍 Key Findings

"""

        for finding in data["findings"]:
            severity_emoji = {
                "critical": "🚨",
                "high": "⚠️",
                "medium": "⚡",
                "low": "💡",
                "info": "ℹ️",
            }.get(finding["severity"], "📋")

            md_content += f"""
### {severity_emoji} {finding["title"]}

**Agent:** {finding["agent"].replace("_", " ").title()}  
**Severity:** {finding["severity"].upper()}  
**Confidence:** {finding["confidence"]:.1f}%

{finding["description"]}

**Recommendation:** {finding["recommendation"]}

---
"""

        md_content += """
## 📋 Recommendations

"""

        for rec in data["recommendations"]:
            md_content += f"- {rec}\n"

        md_content += """
## 🚀 Next Steps

"""

        for step in data["next_steps"]:
            md_content += f"1. {step}\n"

        return md_content

    def display_summary(self, analysis: CollaborativeAnalysis):
        """Display analysis summary in console."""

        # System metrics table
        metrics_table = Table(title="📊 System Metrics")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="magenta")

        metrics_table.add_row(
            "CPU Utilization", f"{analysis.system_metrics.cpu_utilization:.1f}%"
        )
        metrics_table.add_row(
            "Memory Utilization", f"{analysis.system_metrics.memory_utilization:.1f}%"
        )
        metrics_table.add_row(
            "Disk Utilization", f"{analysis.system_metrics.disk_utilization:.1f}%"
        )
        metrics_table.add_row(
            "Process Count", str(analysis.system_metrics.process_count)
        )

        console.print(metrics_table)

        # Findings summary
        severity_counts = {}
        for finding in analysis.findings:
            severity = finding.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        if severity_counts:
            findings_table = Table(title="🔍 Findings Summary")
            findings_table.add_column("Severity", style="cyan")
            findings_table.add_column("Count", style="magenta")

            for severity, count in severity_counts.items():
                emoji = {
                    "critical": "🚨",
                    "high": "⚠️",
                    "medium": "⚡",
                    "low": "💡",
                    "info": "ℹ️",
                }.get(severity, "📋")
                findings_table.add_row(f"{emoji} {severity.title()}", str(count))

            console.print(findings_table)

        # Consensus score
        consensus_panel = Panel(
            f"Consensus Score: {analysis.consensus_score:.1f}%\n"
            f"Total Findings: {len(analysis.findings)}\n"
            f"Recommendations: {len(analysis.recommendations)}",
            title="🤝 Analysis Summary",
            border_style="green",
        )
        console.print(consensus_panel)


async def main():
    """Main demonstration function."""

    console.print(
        Panel.fit(
            "[bold blue]🤖 AutoGen Multi-Agent Performance Analysis Demo[/bold blue]\n"
            "Collaborative analysis with specialized AI agents\n"
            "Based on Brendan Gregg USE Method",
            border_style="blue",
        )
    )

    try:
        # Initialize demo
        demo = AutoGenDemo()

        # Run collaborative analysis
        analysis = await demo.run_collaborative_analysis()

        # Display summary
        demo.display_summary(analysis)

        # Generate reports
        html_report = demo.generate_report(analysis, "html")
        md_report = demo.generate_report(analysis, "markdown")
        json_report = demo.generate_report(analysis, "json")

        console.print(f"\n[green]🎉[/green] Demo completed successfully!")
        console.print(f"[blue]📄[/blue] Reports generated:")
        console.print(f"  • HTML: {html_report}")
        console.print(f"  • Markdown: {md_report}")
        console.print(f"  • JSON: {json_report}")

        # Display top recommendations
        if analysis.recommendations:
            console.print("\n[bold yellow]📋 Top Recommendations:[/bold yellow]")
            for i, rec in enumerate(analysis.recommendations[:5], 1):
                console.print(f"  {i}. {rec}")

    except Exception as e:
        console.print(f"\n[red]❌[/red] Demo failed: {e}")
        logger.error(f"AutoGen demo failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
