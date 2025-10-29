"""
System Performance Analysis Tool

A comprehensive system performance analysis tool based on Brendan Gregg's USE Method
with Domain-Driven Design (DDD) architecture.

Backward compatibility layer for existing imports.
"""

__version__ = "2.0.0"
__author__ = "Reinaldo Saraiva"
__email__ = "reinaldo.saraiva@example.com"

# Legacy imports for backward compatibility
try:
    from .analyzers import USEAnalyzer, USEScore, Status
    from .collectors import SystemCollector
    from .reporters import ReportGenerator
    from .brendan_gregg_persona import BrendanGreggPersona
    from .brendan_llm_agent import BrendanLLMAgent
except ImportError:
    # New DDD structure
    pass

# New DDD imports
from .domain.performance.entities.system_metrics import SystemMetrics
from .domain.performance.entities.performance_insight import PerformanceInsight
from .domain.performance.services.use_method_analyzer import USEMethodAnalyzer
from .domain.performance.services.bottleneck_detector import BottleneckDetector
from .infrastructure.monitoring.psutil_collector import PsutilCollector

__all__ = [
    # Legacy exports
    "USEAnalyzer",
    "USEScore",
    "Status",
    "SystemCollector",
    "ReportGenerator",
    "BrendanGreggPersona",
    "BrendanLLMAgent",
    # New DDD exports
    "SystemMetrics",
    "PerformanceInsight",
    "USEMethodAnalyzer",
    "BottleneckDetector",
    "PsutilCollector",
]
