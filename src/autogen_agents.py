"""
Microsoft AutoGen Multi-Agent System for Performance Analysis

Sistema de agentes especialistas para análise colaborativa de performance
baseado em Brendan Gregg USE Method e context engineering.
"""

import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import uuid

import psutil
import pandas as pd
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# AutoGen imports
try:
    from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
    from autogen.coding import DockerCommandLineCodeExecutor
    from autogen import ConversableAgent, config_list_from_json
except ImportError:
    print("AutoGen not installed. Install with: pip install pyautogen")
    raise

from .collectors import SystemCollector
from .analyzers import USEAnalyzer, LatencyAnalyzer
from .reporters import ReportGenerator

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


class AutoGenPerformanceOrchestrator:
    """Main orchestrator for AutoGen multi-agent performance analysis."""

    def __init__(
        self,
        config_list: Optional[List[Dict[str, Any]]] = None,
        work_dir: Optional[Path] = None,
        enable_code_execution: bool = True,
    ):
        """
        Initialize the AutoGen orchestrator.

        Args:
            config_list: List of LLM configurations
            work_dir: Working directory for code execution
            enable_code_execution: Enable Docker-based code execution
        """
        self.work_dir = work_dir or Path("autogen_workspace")
        self.work_dir.mkdir(exist_ok=True)

        # Initialize system components
        self.collector = SystemCollector()
        self.use_analyzer = USEAnalyzer()
        self.latency_analyzer = LatencyAnalyzer()
        self.report_generator = ReportGenerator()

        # Setup LLM configuration
        self.config_list = config_list or self._get_default_config()

        # Setup code executor
        self.code_executor = None
        if enable_code_execution:
            self.code_executor = DockerCommandLineCodeExecutor(
                work_dir=str(self.work_dir),
                image="python:3.11-slim",
            )

        # Initialize agents
        self.agents = {}
        self.group_chat = None
        self.manager = None

        self._setup_agents()
        self._setup_group_chat()

        console.print("[green]✅[/green] AutoGen Performance Orchestrator initialized")

    def _get_default_config(self) -> List[Dict[str, Any]]:
        """Get default LLM configuration."""
        # Try to get from environment or config file
        try:
            return config_list_from_json("OAI_CONFIG_LIST")
        except:
            # Fallback to environment variables
            return [
                {
                    "model": "gpt-4",
                    "api_key": "your-openai-api-key",  # Set via environment
                },
                {
                    "model": "claude-3-sonnet-20240229",
                    "api_key": "your-anthropic-api-key",
                    "api_type": "anthropic",
                },
            ]

    def _create_system_message(self, role: AgentRole) -> str:
        """Create specialized system message for each agent role."""

        system_messages = {
            AgentRole.PERFORMANCE_ANALYST: """
You are a Senior Performance Analyst with 15+ years of experience in systems performance optimization.

**Your Expertise:**
- Brendan Gregg USE Method (Utilization, Saturation, Errors)
- Linux/Unix performance tuning
- Cloud performance optimization
- Application performance monitoring (APM)
- Performance bottleneck identification

**Your Responsibilities:**
1. Analyze system metrics using USE Method framework
2. Identify performance bottlenecks and anomalies
3. Provide data-driven performance recommendations
4. Validate findings with concrete evidence
5. Consider system-wide performance implications

**Analysis Framework:**
- Utilization: % of time resource is busy
- Saturation: how much work is queued
- Errors: rate of error events
- Always correlate metrics across components
- Consider both immediate and long-term impacts

**Communication Style:**
- Data-driven and evidence-based
- Clear, actionable recommendations
- Include specific metrics and thresholds
- Consider business impact and SLA requirements
""",
            AgentRole.INFRASTRUCTURE_EXPERT: """
You are an Infrastructure Expert with deep knowledge of Linux/Unix systems, cloud architecture, and infrastructure optimization.

**Your Expertise:**
- Linux kernel tuning and optimization
- Container orchestration (Kubernetes, Docker)
- Cloud infrastructure (AWS, Azure, GCP)
- Storage systems and I/O optimization
- Network performance and tuning
- System capacity planning

**Your Responsibilities:**
1. Evaluate infrastructure configuration and optimization
2. Identify architectural bottlenecks
3. Recommend infrastructure improvements
4. Assess scalability and reliability
5. Consider cost-performance trade-offs

**Analysis Focus:**
- System configuration best practices
- Resource allocation and sizing
- Performance tuning opportunities
- Infrastructure security implications
- Disaster recovery and redundancy

**Communication Style:**
- Technical depth with practical focus
- Specific configuration recommendations
- Risk assessment and mitigation
- Long-term infrastructure strategy
""",
            AgentRole.SECURITY_ANALYST: """
You are a Security Analyst specializing in performance-security trade-offs and secure system optimization.

**Your Expertise:**
- OWASP security standards
- System hardening and security monitoring
- Performance impact of security measures
- Vulnerability assessment
- Security incident response

**Your Responsibilities:**
1. Evaluate security implications of performance issues
2. Identify security vulnerabilities affecting performance
3. Recommend secure optimization strategies
4. Assess risk of proposed changes
5. Ensure compliance with security standards

**Security Considerations:**
- Performance impact of security controls
- Security vulnerabilities in system configuration
- Access control and privilege escalation
- Data protection and encryption overhead
- Monitoring and detection capabilities

**Communication Style:**
- Risk-focused analysis
- Clear security recommendations
- Compliance and regulatory considerations
- Balance between security and performance
""",
            AgentRole.COST_OPTIMIZER: """
You are a Cloud Cost Optimization Expert specializing in performance-cost analysis and resource efficiency.

**Your Expertise:**
- Cloud cost analysis and optimization
- Resource rightsizing and efficiency
- Performance-cost trade-offs
- Reserved instances and savings plans
- Multi-cloud cost management

**Your Responsibilities:**
1. Analyze cost implications of performance issues
2. Identify cost optimization opportunities
3. Recommend resource efficiency improvements
4. Calculate ROI of performance investments
5. Optimize cloud spending while maintaining performance

**Cost Analysis Framework:**
- Resource utilization vs. cost
- Performance impact of cost-cutting measures
- Rightsizing recommendations
- Reserved capacity planning
- Multi-cloud cost optimization

**Communication Style:**
- Financial metrics and ROI focus
- Specific cost-saving recommendations
- Risk assessment of cost optimizations
- Long-term cost strategy
""",
            AgentRole.REPORT_GENERATOR: """
You are a Technical Communication Expert specializing in performance analysis reporting and visualization.

**Your Expertise:**
- Technical documentation and reporting
- Data visualization and dashboard design
- Executive summary creation
- Stakeholder communication
- Performance metrics presentation

**Your Responsibilities:**
1. Synthesize findings from all agents
2. Create comprehensive analysis reports
3. Design effective visualizations
4. Tailor communication to different audiences
5. Ensure clarity and actionability

**Report Structure:**
- Executive summary with key findings
- Detailed technical analysis
- Visual representations of data
- Actionable recommendations
- Implementation roadmap

**Communication Style:**
- Clear, concise, and structured
- Appropriate for technical and business audiences
- Visual and data-driven
- Action-oriented and practical
""",
            AgentRole.COORDINATOR: """
You are the Performance Analysis Coordinator responsible for orchestrating the collaborative analysis process.

**Your Responsibilities:**
1. Coordinate agent interactions and workflow
2. Ensure comprehensive analysis coverage
3. Facilitate consensus building
4. Manage analysis priorities and conflicts
5. Synthesize final recommendations

**Coordination Strategy:**
- Ensure all perspectives are considered
- Identify and resolve conflicts
- Maintain analysis focus and scope
- Validate consensus and recommendations
- Ensure actionable outcomes

**Communication Style:**
- Facilitative and collaborative
- Clear process management
- Consensus-building focus
- Results-oriented coordination
""",
        }

        return system_messages.get(role, "You are a performance analysis expert.")

    def _setup_agents(self):
        """Setup all specialized agents."""

        # Create user proxy for code execution
        user_proxy = UserProxyAgent(
            name="UserProxy",
            system_message="You execute code and provide system information when requested.",
            code_execution_config={"executor": self.code_executor}
            if self.code_executor
            else False,
            human_input_mode="NEVER",
        )

        # Create specialized agents
        agent_configs = {
            AgentRole.PERFORMANCE_ANALYST: {
                "name": "PerformanceAnalyst",
                "system_message": self._create_system_message(
                    AgentRole.PERFORMANCE_ANALYST
                ),
            },
            AgentRole.INFRASTRUCTURE_EXPERT: {
                "name": "InfrastructureExpert",
                "system_message": self._create_system_message(
                    AgentRole.INFRASTRUCTURE_EXPERT
                ),
            },
            AgentRole.SECURITY_ANALYST: {
                "name": "SecurityAnalyst",
                "system_message": self._create_system_message(
                    AgentRole.SECURITY_ANALYST
                ),
            },
            AgentRole.COST_OPTIMIZER: {
                "name": "CostOptimizer",
                "system_message": self._create_system_message(AgentRole.COST_OPTIMIZER),
            },
            AgentRole.REPORT_GENERATOR: {
                "name": "ReportGenerator",
                "system_message": self._create_system_message(
                    AgentRole.REPORT_GENERATOR
                ),
            },
            AgentRole.COORDINATOR: {
                "name": "Coordinator",
                "system_message": self._create_system_message(AgentRole.COORDINATOR),
            },
        }

        for role, config in agent_configs.items():
            agent = AssistantAgent(
                llm_config={"config_list": self.config_list}, **config
            )
            self.agents[role] = agent

        self.agents["UserProxy"] = user_proxy

    def _setup_group_chat(self):
        """Setup group chat for agent collaboration."""

        # Define speaker selection method
        agents_list = [
            self.agents[AgentRole.COORDINATOR],
            self.agents[AgentRole.PERFORMANCE_ANALYST],
            self.agents[AgentRole.INFRASTRUCTURE_EXPERT],
            self.agents[AgentRole.SECURITY_ANALYST],
            self.agents[AgentRole.COST_OPTIMIZER],
            self.agents[AgentRole.REPORT_GENERATOR],
        ]

        self.group_chat = GroupChat(
            agents=agents_list,
            messages=[],
            max_round=20,
            speaker_selection_method="round_robin",
        )

        self.manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config={"config_list": self.config_list},
        )

    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""

        console.print("[blue]📊[/blue] Collecting system metrics...")

        # Collect metrics using existing collector
        metrics = self.collector.collect_all()

        # Get additional system info
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        network = psutil.net_io_counters()
        load_avg = psutil.getloadavg()

        system_metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_utilization=cpu_percent,
            memory_utilization=memory.percent,
            disk_utilization=(disk.used / disk.total) * 100,
            network_utilization=0.0,  # Calculate based on interface stats
            load_average=list(load_avg),
            process_count=len(psutil.pids()),
            context_switches=0,  # Get from /proc/stat
            disk_io={
                "read_bytes": disk.used,
                "write_bytes": 0,
            },
            network_io={
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
            },
            custom_metrics=metrics,
        )

        console.print("[green]✅[/green] System metrics collected")
        return system_metrics

    def _create_analysis_context(
        self, metrics: SystemMetrics
    ) -> PerformanceAnalysisContext:
        """Create analysis context for agents."""

        import platform
        import os

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

        # Start collaborative analysis
        analysis_prompt = f"""
PERFORMANCE ANALYSIS REQUEST

System Metrics:
{json.dumps(asdict(metrics), indent=2, default=str)}

Analysis Context:
{json.dumps(context.dict(), indent=2, default=str)}

Analysis Scope: {analysis_scope or "All components"}

Please conduct a comprehensive collaborative analysis following this workflow:

1. **Coordinator**: Provide analysis overview and coordinate the process
2. **Performance Analyst**: Analyze metrics using USE method, identify bottlenecks
3. **Infrastructure Expert**: Evaluate infrastructure optimization opportunities
4. **Security Analyst**: Assess security implications and vulnerabilities
5. **Cost Optimizer**: Analyze cost optimization potential
6. **Report Generator**: Synthesize findings and create comprehensive summary

Each agent should:
- Provide specific, data-driven analysis
- Include concrete recommendations
- Consider cross-functional impacts
- Rate confidence in findings (0-100%)
- Identify any conflicts with other agents

Focus on actionable insights that can improve system performance while considering security, cost, and reliability.
"""

        try:
            # Start the group chat
            result = await self.agents[AgentRole.COORDINATOR].a_initiate_chat(
                self.manager,
                message=analysis_prompt,
                max_turns=15,
            )

            # Parse results and create collaborative analysis
            findings = self._parse_agent_findings(result.chat_history)
            recommendations = self._extract_recommendations(result.chat_history)
            consensus_score = self._calculate_consensus_score(findings)

            collaborative_analysis = CollaborativeAnalysis(
                session_id=session_id,
                timestamp=datetime.now(),
                system_metrics=metrics,
                findings=findings,
                consensus_score=consensus_score,
                recommendations=recommendations,
                next_steps=self._generate_next_steps(findings),
                agent_interactions=result.chat_history,
            )

            console.print(
                f"[green]✅[/green] Collaborative analysis completed (Consensus: {consensus_score:.1f}%)"
            )
            return collaborative_analysis

        except Exception as e:
            console.print(f"[red]❌[/red] Analysis failed: {e}")
            logger.error(f"Collaborative analysis failed: {e}", exc_info=True)
            raise

    def _parse_agent_findings(
        self, chat_history: List[Dict[str, Any]]
    ) -> List[AnalysisFinding]:
        """Parse agent findings from chat history."""

        findings = []

        for message in chat_history:
            if "content" in message and "name" in message:
                agent_name = message["name"]
                content = message["content"]

                # Map agent name to role
                role_mapping = {
                    "PerformanceAnalyst": AgentRole.PERFORMANCE_ANALYST,
                    "InfrastructureExpert": AgentRole.INFRASTRUCTURE_EXPERT,
                    "SecurityAnalyst": AgentRole.SECURITY_ANALYST,
                    "CostOptimizer": AgentRole.COST_OPTIMIZER,
                    "ReportGenerator": AgentRole.REPORT_GENERATOR,
                    "Coordinator": AgentRole.COORDINATOR,
                }

                role = role_mapping.get(agent_name)
                if role:
                    # Extract findings from message (simplified parsing)
                    # In production, use more sophisticated NLP parsing
                    finding = AnalysisFinding(
                        id=str(uuid.uuid4()),
                        agent=role,
                        component="system",  # Extract from content
                        severity=AnalysisSeverity.MEDIUM,  # Extract from content
                        title=f"Analysis from {agent_name}",
                        description=content[:500],  # Truncate for demo
                        recommendation="",  # Extract from content
                        metrics={},  # Extract from content
                        confidence=0.8,  # Extract from content
                        timestamp=datetime.now(),
                    )
                    findings.append(finding)

        return findings

    def _extract_recommendations(self, chat_history: List[Dict[str, Any]]) -> List[str]:
        """Extract recommendations from chat history."""

        recommendations = []

        # Simple extraction - in production, use more sophisticated parsing
        for message in chat_history:
            if "content" in message:
                content = message["content"].lower()
                if "recommend" in content or "suggest" in content:
                    # Extract sentences with recommendations
                    sentences = content.split(".")
                    for sentence in sentences:
                        if any(
                            word in sentence
                            for word in ["recommend", "suggest", "should", "implement"]
                        ):
                            recommendations.append(sentence.strip())

        return recommendations[:10]  # Limit to top 10

    def _calculate_consensus_score(self, findings: List[AnalysisFinding]) -> float:
        """Calculate consensus score among agents."""

        if not findings:
            return 0.0

        # Simple consensus calculation based on confidence scores
        total_confidence = sum(finding.confidence for finding in findings)
        avg_confidence = total_confidence / len(findings)

        # Adjust based on agent agreement (simplified)
        agent_roles = set(finding.agent for finding in findings)
        diversity_bonus = min(len(agent_roles) / 5, 1.0) * 10

        return min(avg_confidence + diversity_bonus, 100.0)

    def _generate_next_steps(self, findings: List[AnalysisFinding]) -> List[str]:
        """Generate next steps based on findings."""

        next_steps = []

        # Group findings by severity
        critical_findings = [
            f for f in findings if f.severity == AnalysisSeverity.CRITICAL
        ]
        high_findings = [f for f in findings if f.severity == AnalysisSeverity.HIGH]

        if critical_findings:
            next_steps.append("Address critical performance issues immediately")

        if high_findings:
            next_steps.append(
                "Plan infrastructure optimizations for high-priority findings"
            )

        next_steps.extend(
            [
                "Implement monitoring for identified metrics",
                "Schedule follow-up analysis in 24 hours",
                "Create implementation roadmap for recommendations",
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

        # Generate report using existing report generator
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
    <title>Collaborative Performance Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
        .metric-card { background: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #007cba; }
        .finding { margin: 15px 0; padding: 15px; border-radius: 5px; }
        .critical { border-left: 4px solid #d32f2f; background: #ffebee; }
        .high { border-left: 4px solid #f57c00; background: #fff3e0; }
        .medium { border-left: 4px solid #fbc02d; background: #fffde7; }
        .low { border-left: 4px solid #388e3c; background: #e8f5e8; }
        .agent-section { margin: 30px 0; padding: 20px; background: #f5f5f5; border-radius: 5px; }
        .consensus { font-size: 24px; font-weight: bold; color: #007cba; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Collaborative Performance Analysis Report</h1>
        <p><strong>Session ID:</strong> {session_id}</p>
        <p><strong>Generated:</strong> {timestamp}</p>
        <p><strong>Consensus Score:</strong> <span class="consensus">{consensus_score:.1f}%</span></p>
    </div>

    <h2>📊 System Metrics</h2>
    <div class="metrics">
        <div class="metric-card">
            <h3>CPU Utilization</h3>
            <p style="font-size: 24px; color: #007cba;">{cpu_utilization:.1f}%</p>
        </div>
        <div class="metric-card">
            <h3>Memory Utilization</h3>
            <p style="font-size: 24px; color: #007cba;">{memory_utilization:.1f}%</p>
        </div>
        <div class="metric-card">
            <h3>Disk Utilization</h3>
            <p style="font-size: 24px; color: #007cba;">{disk_utilization:.1f}%</p>
        </div>
        <div class="metric-card">
            <h3>Process Count</h3>
            <p style="font-size: 24px; color: #007cba;">{process_count}</p>
        </div>
    </div>

    <h2>🔍 Key Findings</h2>
    {findings_html}

    <h2>👥 Agent Analysis Summary</h2>
    {agent_summary_html}

    <h2>📋 Recommendations</h2>
    <ul>
        {recommendations_html}
    </ul>

    <h2>🚀 Next Steps</h2>
    <ol>
        {next_steps_html}
    </ol>
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
                <p><strong>Agent:</strong> {finding["agent"]}</p>
                <p><strong>Severity:</strong> {finding["severity"].upper()}</p>
                <p><strong>Confidence:</strong> {finding["confidence"]:.1f}%</p>
                <p>{finding["description"]}</p>
            </div>
            """

        # Generate agent summary HTML
        agent_summary_html = ""
        for agent, summary in data["agent_summary"].items():
            agent_summary_html += f"""
            <div class="agent-section">
                <h3>{agent.replace("_", " ").title()}</h3>
                <p><strong>Findings:</strong> {summary["findings_count"]}</p>
                <p><strong>Average Confidence:</strong> {summary["avg_confidence"]:.1f}%</p>
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
            md_content += f"""
### {finding["title"]}

**Agent:** {finding["agent"]}  
**Severity:** {finding["severity"].upper()}  
**Confidence:** {finding["confidence"]:.1f}%

{finding["description"]}

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
        if self.code_executor:
            await self.code_executor.stop()

        console.print("[blue]🧹[/blue] AutoGen orchestrator cleaned up")


# CLI Integration
async def main_autogen_analysis():
    """Main function for AutoGen analysis."""

    console.print(
        Panel.fit(
            "[bold blue]🤖 AutoGen Multi-Agent Performance Analysis[/bold blue]\n"
            "Collaborative analysis with specialized AI agents",
            border_style="blue",
        )
    )

    try:
        # Initialize orchestrator
        orchestrator = AutoGenPerformanceOrchestrator()

        # Run collaborative analysis
        analysis = await orchestrator.run_collaborative_analysis()

        # Generate report
        report_path = orchestrator.generate_comprehensive_report(analysis, "html")

        # Display summary
        console.print(f"\n[green]🎉[/green] Analysis completed successfully!")
        console.print(f"[blue]📄[/blue] Report available at: {report_path}")
        console.print(
            f"[yellow]🤝[/yellow] Consensus Score: {analysis.consensus_score:.1f}%"
        )

        # Cleanup
        await orchestrator.cleanup()

    except Exception as e:
        console.print(f"\n[red]❌[/red] Analysis failed: {e}")
        logger.error(f"AutoGen analysis failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main_autogen_analysis())
