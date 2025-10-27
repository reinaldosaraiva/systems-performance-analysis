"""
AutoGen Integration for Systems Performance Analysis

Integration module that provides multi-agent analysis capabilities
using Microsoft AutoGen framework for collaborative performance analysis.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import uuid
import random

import psutil
import pandas as pd
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from collectors import SystemCollector
    from analyzers import USEAnalyzer, LatencyAnalyzer
    from reporters_simple import ReportGenerator
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running this from the project root directory")
    sys.exit(1)

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
    custom_metrics: Optional[Dict[str, Any]] = None


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


class PerformanceAnalysisContext(BaseModel):
    """Context model for performance analysis."""

    system_info: Dict[str, Any] = Field(default_factory=dict)
    current_metrics: Dict[str, float] = Field(default_factory=dict)
    historical_data: Optional[List[Dict[str, Any]]] = None
    analysis_goals: List[str] = Field(default_factory=list)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    environment: str = "production"
    sla_requirements: Dict[str, float] = Field(default_factory=dict)


class MockAgent:
    """Mock agent for demonstration purposes."""

    def __init__(self, name: str, role: AgentRole, system_message: str):
        self.name = name
        self.role = role
        self.system_message = system_message

    async def analyze(
        self, metrics: SystemMetrics, context: PerformanceAnalysisContext
    ) -> List[AnalysisFinding]:
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


class AutoGenIntegration:
    """AutoGen integration for performance analysis."""

    def __init__(self, work_dir: Optional[Path] = None):
        """Initialize the AutoGen integration."""
        self.work_dir = work_dir or Path("autogen_workspace")
        self.work_dir.mkdir(exist_ok=True)

        # Initialize system components
        try:
            self.collector = SystemCollector()
            self.use_analyzer = USEAnalyzer()
            self.latency_analyzer = LatencyAnalyzer()
            self.report_generator = ReportGenerator()
        except Exception as e:
            console.print(
                f"[yellow]⚠️[/yellow] Warning: Could not initialize system components: {e}"
            )
            self.collector = None
            self.use_analyzer = None
            self.latency_analyzer = None
            self.report_generator = None

        # Initialize mock agents
        self.agents = self._setup_mock_agents()

        console.print("[green]✅[/green] AutoGen Integration initialized")

    def _setup_mock_agents(self) -> Dict[AgentRole, MockAgent]:
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

        # Get system metrics directly
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        network = psutil.net_io_counters()

        try:
            load_avg = psutil.getloadavg()
        except (AttributeError, OSError):
            # Windows doesn't have getloadavg
            load_avg = [0.0, 0.0, 0.0]

        # Try to collect additional metrics using the collector
        custom_metrics = {}
        if self.collector:
            try:
                custom_metrics = self.collector.collect_all()
            except Exception as e:
                console.print(
                    f"[yellow]⚠️[/yellow] Could not collect custom metrics: {e}"
                )

        system_metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_utilization=cpu_percent,
            memory_utilization=memory.percent,
            disk_utilization=(disk.used / disk.total) * 100,
            network_utilization=0.0,  # Calculate based on interface stats
            load_average=list(load_avg),
            process_count=len(psutil.pids()),
            context_switches=0,  # Get from /proc/stat on Linux
            disk_io={
                "read_bytes": disk.used,
                "write_bytes": 0,
            },
            network_io={
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
            },
            custom_metrics=custom_metrics,
        )

        console.print("[green]✅[/green] System metrics collected")
        return system_metrics

    def _create_analysis_context(
        self, metrics: SystemMetrics
    ) -> PerformanceAnalysisContext:
        """Create analysis context for agents."""

        import platform

        return PerformanceAnalysisContext(
            system_info={
                "hostname": platform.node(),
                "platform": platform.system(),
                "architecture": platform.machine(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
            },
            current_metrics={
                "cpu_utilization": float(metrics.cpu_utilization),
                "memory_utilization": float(metrics.memory_utilization),
                "disk_utilization": float(metrics.disk_utilization),
                "load_average_1m": float(metrics.load_average[0])
                if metrics.load_average
                else 0.0,
                "process_count": float(metrics.process_count),
            },
            analysis_goals=[
                "Identify performance bottlenecks using USE method",
                "Assess infrastructure optimization opportunities",
                "Evaluate security implications",
                "Analyze cost optimization potential",
                "Generate actionable recommendations",
            ],
            environment="production",
            sla_requirements={
                "cpu_utilization_max": 80.0,
                "memory_utilization_max": 85.0,
                "disk_utilization_max": 90.0,
                "load_average_per_cpu": 2.0,
            },
        )

    async def run_collaborative_analysis(
        self,
        metrics: Optional[SystemMetrics] = None,
        analysis_scope: Optional[List[str]] = None,
    ) -> CollaborativeAnalysis:
        """
        Run collaborative performance analysis with all agents.

        Args:
            metrics: Pre-collected system metrics
            analysis_scope: Specific components to analyze

        Returns:
            CollaborativeAnalysis with all findings and recommendations
        """

        session_id = str(uuid.uuid4())
        console.print(
            f"[blue]🚀[/blue] Starting collaborative analysis (Session: {session_id[:8]})"
        )

        # Collect metrics if not provided
        if metrics is None:
            metrics = await self.collect_system_metrics()

        # Create analysis context
        context = self._create_analysis_context(metrics)

        # Run analysis with all agents
        all_findings = []
        agent_interactions = []

        for role, agent in self.agents.items():
            console.print(f"[yellow]🤖[/yellow] Running {agent.name} analysis...")

            # Simulate agent interaction
            interaction = {
                "agent": agent.name,
                "role": role.value,
                "timestamp": datetime.now().isoformat(),
                "message": f"Starting {role.value} analysis...",
            }
            agent_interactions.append(interaction)

            # Get findings from agent
            findings = await agent.analyze(metrics, context)
            all_findings.extend(findings)

            # Record completion
            interaction = {
                "agent": agent.name,
                "role": role.value,
                "timestamp": datetime.now().isoformat(),
                "message": f"Completed {role.value} analysis with {len(findings)} findings.",
            }
            agent_interactions.append(interaction)

            console.print(
                f"[green]✅[/green] {agent.name} completed ({len(findings)} findings)"
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

    def generate_comprehensive_report(
        self, analysis: CollaborativeAnalysis, format: str = "html"
    ) -> Path:
        """
        Generate comprehensive report from collaborative analysis.

        Args:
            analysis: Collaborative analysis results
            format: Report format (html, markdown, json)

        Returns:
            Path to generated report
        """

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
            "agent_summary": self._generate_agent_summary(analysis.findings),
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
        filename = f"collaborative_analysis_{timestamp}.{extension}"
        report_path = Path("reports") / filename
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        console.print(f"[green]✅[/green] Report saved to: {report_path}")
        return report_path

    def _generate_agent_summary(
        self, findings: List[AnalysisFinding]
    ) -> Dict[str, Any]:
        """Generate summary by agent."""

        agent_summary = {}

        for finding in findings:
            agent = finding.agent.value
            if agent not in agent_summary:
                agent_summary[agent] = {
                    "findings_count": 0,
                    "severity_distribution": {},
                    "avg_confidence": 0.0,
                    "key_recommendations": [],
                }

            agent_summary[agent]["findings_count"] += 1

            severity = finding.severity.value
            agent_summary[agent]["severity_distribution"][severity] = (
                agent_summary[agent]["severity_distribution"].get(severity, 0) + 1
            )

        # Calculate average confidence per agent
        for agent in agent_summary:
            agent_findings = [f for f in findings if f.agent.value == agent]
            if agent_findings:
                avg_conf = sum(f.confidence for f in agent_findings) / len(
                    agent_findings
                )
                agent_summary[agent]["avg_confidence"] = avg_conf

        return agent_summary

    def _generate_html_report(self, data: Dict[str, Any]) -> str:
        """Generate HTML report from analysis data."""

        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>🤖 Collaborative Performance Analysis Report</title>
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
        .finding { 
            margin: 25px 0; 
            padding: 25px; 
            border-radius: 10px; 
            border-left: 5px solid;
            background: #f8f9fa;
            transition: transform 0.2s;
        }
        .finding:hover { transform: translateX(5px); }
        .critical { border-left-color: #dc3545; background: #f8d7da; }
        .high { border-left-color: #fd7e14; background: #fff3cd; }
        .medium { border-left-color: #ffc107; background: #fffde7; }
        .low { border-left-color: #28a745; background: #d4edda; }
        .info { border-left-color: #17a2b8; background: #d1ecf1; }
        .finding h4 { margin: 0 0 15px 0; color: #495057; }
        .finding p { margin: 10px 0; line-height: 1.6; }
        .agent-section { 
            margin: 30px 0; 
            padding: 25px; 
            background: #f8f9fa; 
            border-radius: 10px;
            border: 1px solid #e9ecef;
        }
        .consensus { 
            font-size: 3em; 
            font-weight: bold; 
            color: #007cba; 
            text-align: center;
            margin: 30px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        .section-title { 
            font-size: 2em; 
            color: #495057; 
            margin: 50px 0 30px 0; 
            text-align: center;
            position: relative;
            padding-bottom: 15px;
        }
        .section-title::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 80px;
            height: 3px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
        }
        .recommendations, .next-steps {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            border: 1px solid #e9ecef;
        }
        .recommendations ul, .next-steps ol {
            margin: 0;
            padding-left: 20px;
        }
        .recommendations li, .next-steps li {
            margin: 15px 0;
            line-height: 1.6;
        }
        .severity-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .severity-critical { background: #dc3545; color: white; }
        .severity-high { background: #fd7e14; color: white; }
        .severity-medium { background: #ffc107; color: black; }
        .severity-low { background: #28a745; color: white; }
        .severity-info { background: #17a2b8; color: white; }
        .agent-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .agent-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #e9ecef;
            text-align: center;
        }
        .agent-card h4 {
            margin: 0 0 15px 0;
            color: #007cba;
        }
        @media (max-width: 768px) {
            .content { padding: 20px; }
            .header { padding: 30px 20px; }
            .header h1 { font-size: 2em; }
            .metrics { grid-template-columns: 1fr; }
            .agent-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Collaborative Performance Analysis</h1>
            <p><strong>Session:</strong> {session_id}</p>
            <p><strong>Generated:</strong> {timestamp}</p>
            <div class="consensus">{consensus_score:.0f}% Consensus</div>
        </div>

        <div class="content">
            <h2 class="section-title">📊 System Metrics</h2>
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
                    <h3>Process Count</h3>
                    <div class="value">{process_count}</div>
                </div>
            </div>

            <h2 class="section-title">🔍 Key Findings</h2>
            {findings_html}

            <h2 class="section-title">👥 Agent Analysis Summary</h2>
            <div class="agent-grid">
                {agent_summary_html}
            </div>

            <h2 class="section-title">📋 Recommendations</h2>
            <div class="recommendations">
                <ul>
                    {recommendations_html}
                </ul>
            </div>

            <h2 class="section-title">🚀 Next Steps</h2>
            <div class="next-steps">
                <ol>
                    {next_steps_html}
                </ol>
            </div>
        </div>
    </div>
</body>
</html>
        """

        # Generate findings HTML
        findings_html = ""
        for finding in data["findings"]:
            severity_class = finding["severity"]
            findings_html += f"""
            <div class="finding {severity_class}">
                <h4>{finding["title"]}</h4>
                <p><strong>Agent:</strong> {finding["agent"].replace("_", " ").title()}</p>
                <p><strong>Severity:</strong> <span class="severity-badge severity-{severity_class}">{finding["severity"]}</span></p>
                <p><strong>Confidence:</strong> {finding["confidence"]:.1f}%</p>
                <p>{finding["description"]}</p>
                <p><strong>💡 Recommendation:</strong> {finding["recommendation"]}</p>
            </div>
            """

        # Generate agent summary HTML
        agent_summary_html = ""
        for agent, summary in data["agent_summary"].items():
            agent_summary_html += f"""
            <div class="agent-card">
                <h4>{agent.replace("_", " ").title()}</h4>
                <p><strong>Findings:</strong> {summary["findings_count"]}</p>
                <p><strong>Avg Confidence:</strong> {summary["avg_confidence"]:.1f}%</p>
            </div>
            """

        # Generate recommendations HTML
        recommendations_html = "\n".join(
            f"<li>{rec}</li>" for rec in data["recommendations"]
        )

        # Generate next steps HTML
        next_steps_html = "\n".join(f"<li>{step}</li>" for step in data["next_steps"])

        return html_template.format(
            session_id=data["session_id"],
            timestamp=data["timestamp"],
            consensus_score=data["consensus_score"],
            cpu_utilization=data["system_metrics"]["cpu_utilization"],
            memory_utilization=data["system_metrics"]["memory_utilization"],
            disk_utilization=data["system_metrics"]["disk_utilization"],
            process_count=data["system_metrics"]["process_count"],
            findings_html=findings_html,
            agent_summary_html=agent_summary_html,
            recommendations_html=recommendations_html,
            next_steps_html=next_steps_html,
        )

    def _generate_markdown_report(self, data: Dict[str, Any]) -> str:
        """Generate Markdown report from analysis data."""

        md_content = f"""
# 🤖 Collaborative Performance Analysis Report

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
| Load Average | {data["system_metrics"]["load_average"]} |

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

**💡 Recommendation:** {finding["recommendation"]}

---
"""

        md_content += """
## 👥 Agent Analysis Summary

"""

        for agent, summary in data["agent_summary"].items():
            md_content += f"""
### {agent.replace("_", " ").title()}

- **Findings:** {summary["findings_count"]}
- **Average Confidence:** {summary["avg_confidence"]:.1f}%

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

    async def cleanup(self):
        """Cleanup resources."""
        console.print("[blue]🧹[/blue] AutoGen integration cleaned up")


# CLI Integration
async def main_autogen_integration():
    """Main function for AutoGen integration."""

    console.print(
        Panel.fit(
            "[bold blue]🤖 AutoGen Multi-Agent Performance Analysis[/bold blue]\n"
            "Collaborative analysis with specialized AI agents\n"
            "Integrated with existing systems performance tool",
            border_style="blue",
        )
    )

    try:
        # Initialize AutoGen integration
        autogen = AutoGenIntegration()

        # Run collaborative analysis
        analysis = await autogen.run_collaborative_analysis()

        # Generate reports in multiple formats
        html_report = autogen.generate_comprehensive_report(analysis, "html")
        md_report = autogen.generate_comprehensive_report(analysis, "markdown")
        json_report = autogen.generate_comprehensive_report(analysis, "json")

        # Display summary
        console.print(f"\n[green]🎉[/green] Analysis completed successfully!")
        console.print(f"[blue]📄[/blue] HTML Report: {html_report}")
        console.print(f"[blue]📄[/blue] Markdown Report: {md_report}")
        console.print(f"[blue]📄[/blue] JSON Report: {json_report}")
        console.print(
            f"[yellow]🤝[/yellow] Consensus Score: {analysis.consensus_score:.1f}%"
        )
        console.print(f"[cyan]📊[/cyan] Total Findings: {len(analysis.findings)}")

        # Display findings summary
        severity_counts = {}
        for finding in analysis.findings:
            severity = finding.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        if severity_counts:
            console.print("\n[bold]Findings by Severity:[/bold]")
            for severity, count in severity_counts.items():
                emoji = {
                    "critical": "🚨",
                    "high": "⚠️",
                    "medium": "⚡",
                    "low": "💡",
                    "info": "ℹ️",
                }.get(severity, "📋")
                console.print(f"  {emoji} {severity.title()}: {count}")

        # Display top recommendations
        if analysis.recommendations:
            console.print("\n[bold]Top Recommendations:[/bold]")
            for i, rec in enumerate(analysis.recommendations[:5], 1):
                console.print(f"  {i}. {rec}")

        # Cleanup
        await autogen.cleanup()

    except Exception as e:
        console.print(f"\n[red]❌[/red] Analysis failed: {e}")
        logger.error(f"AutoGen integration failed: {e}", exc_info=True)


# Remote execution support
async def run_remote_analysis(
    target_host: str, target_user: str = "ubuntu"
) -> CollaborativeAnalysis:
    """Run analysis on remote host without cloning code."""

    console.print(
        f"[blue]🌐[/blue] Running remote analysis on {target_user}@{target_host}"
    )

    # Create remote agent script
    remote_script = f'''
import asyncio
import json
import sys
from datetime import datetime

# Install uv if not present
import subprocess
import os

def ensure_uv():
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing uv...")
        subprocess.run("curl -LsSf https://astral.sh/uv/install.sh | sh", shell=True, check=True)
        os.environ["PATH"] = os.path.expanduser("~/.local/bin:") + os.environ.get("PATH", "")

async def collect_and_analyze():
    """Collect metrics and run analysis on remote system."""
    ensure_uv()
    
    # Install required packages
    packages = ["psutil", "pydantic", "rich", "pandas", "matplotlib"]
    for pkg in packages:
        try:
            subprocess.run(["uv", "add", pkg], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            pass  # Package might already be installed
    
    # Import and run analysis
    import psutil
    from datetime import datetime
    
    # Collect basic metrics
    metrics = {{
        "timestamp": datetime.now().isoformat(),
        "cpu_utilization": psutil.cpu_percent(interval=1),
        "memory_utilization": psutil.virtual_memory().percent,
        "disk_utilization": (psutil.disk_usage("/").used / psutil.disk_usage("/").total) * 100,
        "process_count": len(psutil.pids()),
        "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0, 0, 0],
        "hostname": psutil.os.uname().nodename if hasattr(psutil.os, 'uname') else "unknown"
    }}
    
    return metrics

if __name__ == "__main__":
    result = asyncio.run(collect_and_analyze())
    print(json.dumps(result))
'''

    # Execute script remotely and get results
    import tempfile
    import subprocess

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(remote_script)
        script_path = f.name

    try:
        # Copy script to remote and execute
        remote_script_path = "/tmp/remote_analysis.py"

        # Copy script
        subprocess.run(
            ["scp", script_path, f"{target_user}@{target_host}:{remote_script_path}"],
            check=True,
        )

        # Execute script
        result = subprocess.run(
            [
                "ssh",
                f"{target_user}@{target_host}",
                f"cd /tmp && python3 {remote_script_path}",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        # Parse results
        remote_metrics = json.loads(result.stdout)

        # Create SystemMetrics from remote data
        system_metrics = SystemMetrics(
            timestamp=datetime.fromisoformat(remote_metrics["timestamp"]),
            cpu_utilization=remote_metrics["cpu_utilization"],
            memory_utilization=remote_metrics["memory_utilization"],
            disk_utilization=remote_metrics["disk_utilization"],
            network_utilization=0.0,  # Not collected in remote script
            load_average=remote_metrics["load_average"],
            process_count=remote_metrics["process_count"],
            context_switches=0,
            disk_io={},
            network_io={},
        )

        # Run local AutoGen analysis with remote metrics
        autogen = AutoGenIntegration()
        analysis = await autogen.run_collaborative_analysis(system_metrics)

        console.print(f"[green]✅[/green] Remote analysis completed for {target_host}")
        return analysis

    finally:
        # Cleanup
        import os

        os.unlink(script_path)
        try:
            subprocess.run(
                ["ssh", f"{target_user}@{target_host}", f"rm -f {remote_script_path}"],
                stderr=subprocess.DEVNULL,
            )
        except:
            pass  # Ignore cleanup errors


if __name__ == "__main__":
    asyncio.run(main_autogen_integration())
