"""
System Performance Analyzers

Implementação do USE Method e análise de latência baseada em Brendan Gregg.
Seguindo padrões de context engineering e regras do CLAUDE.md.
"""

import logging
import statistics
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class Status(Enum):
    """Status codes para análise USE."""

    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class USEScore:
    """Score do USE Method para um componente."""

    utilization: float  # 0-100%
    saturation: float  # 0-100%
    errors: float  # 0-100%
    overall_score: float  # 0-100%
    status: Status
    recommendations: List[str]


class USEAnalyzer:
    """Analisador baseado no USE Method de Brendan Gregg."""

    # Thresholds padrão baseados em best practices
    THRESHOLDS = {
        "cpu": {"utilization": 80, "saturation": 20, "errors": 0},
        "memory": {"utilization": 85, "saturation": 10, "errors": 0},
        "disk": {"utilization": 70, "saturation": 30, "errors": 0},
        "network": {"utilization": 80, "saturation": 15, "errors": 0},
    }

    def __init__(self, custom_thresholds: Optional[Dict[str, Dict[str, float]]] = None):
        """
        Inicializa o analisador USE.

        Args:
            custom_thresholds: Thresholds customizados por componente
        """
        if custom_thresholds:
            self.thresholds = {**self.THRESHOLDS, **custom_thresholds}
        else:
            self.thresholds = self.THRESHOLDS

    def analyze_system(self, metrics: Dict[str, Dict[str, Any]]) -> Dict[str, USEScore]:
        """
        Analisa todos os componentes do sistema usando USE Method.

        Args:
            metrics: Métricas coletadas do sistema

        Returns:
            Scores USE para cada componente
        """
        logger.info("Starting USE Method analysis")
        results = {}

        for component, data in metrics.items():
            if component in self.thresholds and "error" not in data:
                try:
                    score = self._analyze_component(component, data)
                    results[component] = score
                    logger.debug(
                        f"{component} USE score: {score.overall_score:.1f}% ({score.status.value})"
                    )
                except Exception as e:
                    logger.error(f"Failed to analyze {component}: {e}")
                    results[component] = USEScore(
                        utilization=0,
                        saturation=0,
                        errors=100,
                        overall_score=100,
                        status=Status.CRITICAL,
                        recommendations=[f"Analysis failed: {e}"],
                    )
            else:
                logger.debug(
                    f"Skipping {component}: no thresholds defined or error in metrics"
                )

        return results

    def _analyze_component(self, component: str, data: Dict[str, Any]) -> USEScore:
        """
        Analisa um componente específico usando USE Method.

        Args:
            component: Nome do componente
            data: Métricas do componente

        Returns:
            Score USE para o componente
        """
        thresholds = self.thresholds[component]

        # Calcular métricas USE
        utilization = self._calculate_utilization(component, data)
        saturation = self._calculate_saturation(component, data)
        errors = self._calculate_errors(component, data)

        # Limitar a 100%
        utilization = min(utilization, 100)
        saturation = min(saturation, 100)
        errors = min(errors, 100)

        # Calcular score geral (máximo das três métricas)
        overall_score = max(utilization, saturation, errors)

        # Determinar status
        status = self._determine_status(utilization, saturation, errors, thresholds)

        # Gerar recomendações
        recommendations = self._generate_recommendations(
            component, utilization, saturation, errors, status
        )

        return USEScore(
            utilization=utilization,
            saturation=saturation,
            errors=errors,
            overall_score=overall_score,
            status=status,
            recommendations=recommendations,
        )

    def _calculate_utilization(self, component: str, data: Dict[str, Any]) -> float:
        """Calcula utilization para um componente."""
        if component == "cpu":
            return data.get("utilization", 0)
        elif component == "memory":
            return data.get("utilization", 0)
        elif component == "disk":
            return data.get("total_utilization", 0)
        elif component == "network":
            # Network utilization é mais complexa - usar throughput como proxy
            interfaces = data.get("interfaces", {})
            if interfaces:
                # Simplificação: usar média de utilização se disponível
                return 50.0  # Placeholder - requer baseline
            return 0
        return 0

    def _calculate_saturation(self, component: str, data: Dict[str, Any]) -> float:
        """Calcula saturation para um componente."""
        if component == "cpu":
            return data.get("saturation", 0)
        elif component == "memory":
            return data.get("saturation", 0)
        elif component == "disk":
            return data.get("saturation", 0)
        elif component == "network":
            return data.get("saturation", 0)
        return 0

    def _calculate_errors(self, component: str, data: Dict[str, Any]) -> float:
        """Calcula error rate para um componente."""
        if component == "cpu":
            # CPU errors são raros - usar context switches异常 como proxy
            return 0  # Placeholder
        elif component == "memory":
            # Memory errors (OOM, allocation failures)
            return 0  # Placeholder
        elif component == "disk":
            # Disk I/O errors
            io_metrics = data.get("io", {})
            # Simplificação - requer dados históricos
            return 0
        elif component == "network":
            return data.get("errors", 0)
        return 0

    def _determine_status(
        self,
        utilization: float,
        saturation: float,
        errors: float,
        thresholds: Dict[str, Any],
    ) -> Status:
        """Determina status baseado nos thresholds."""
        if errors > thresholds["errors"]:
            return Status.CRITICAL
        elif (
            utilization > thresholds["utilization"]
            or saturation > thresholds["saturation"]
        ):
            return Status.WARNING
        else:
            return Status.OK

    def _generate_recommendations(
        self,
        component: str,
        utilization: float,
        saturation: float,
        errors: float,
        status: Status,
    ) -> List[str]:
        """Gera recomendações baseadas na análise."""
        recommendations = []

        if component == "cpu":
            if utilization > 80:
                recommendations.append(
                    "🔥 CPU alta (>80%): Considere scale-up horizontal ou "
                    "otimização de algoritmos. Em projetos de cloud, "
                    "review de auto-scaling policies recomendado."
                )
            if saturation > 20:
                recommendations.append(
                    "⚡ CPU saturada: Load average elevado indica "
                    "processamento excessivo. Verifique processos CPU-bound "
                    "e considere otimização ou distribuição de carga."
                )

        elif component == "memory":
            if utilization > 85:
                recommendations.append(
                    "💾 Memória alta (>85%): Risco de OOM. Considere "
                    "aumentar RAM ou otimizar uso de memória. "
                    "Em containers, review de memory limits recomendado."
                )
            if saturation > 10:
                recommendations.append(
                    "🔄 Swap ativo: Performance degradada. "
                    "Aumente RAM física ou otimize aplicações memory-intensive."
                )

        elif component == "disk":
            if utilization > 70:
                recommendations.append(
                    "💿 Disco cheio (>70%): Risco de falta de espaço. "
                    "Implemente cleanup automático e monitoramento. "
                    "Em cloud, considere storage expansion."
                )
            if saturation > 30:
                recommendations.append(
                    "⏱️ I/O saturado: Disk bottleneck detectado. "
                    "Considere SSD upgrade, RAID optimization ou "
                    "distribuição de I/O across multiple disks."
                )

        elif component == "network":
            if errors > 0:
                recommendations.append(
                    "❌ Erros de rede: Packet drops detectados. "
                    "Verifique configurações de rede, hardware e "
                    "firewall rules. Em cloud, review de security groups."
                )
            if saturation > 15:
                recommendations.append(
                    "🌐 Rede saturada: Bandwidth limit reached. "
                    "Considere link upgrade ou load balancing. "
                    "Monitore padrões de tráfego para otimização."
                )

        # Recomendações gerais baseadas no status
        if status == Status.CRITICAL:
            recommendations.append(
                "🚨 CRITICAL: Ação imediata necessária! "
                "Sistema em risco de degradação severa."
            )
        elif status == Status.WARNING:
            recommendations.append(
                "⚠️ WARNING: Monitoramento próximo recomendado. "
                "Planeje ações corretivas preventivas."
            )
        else:
            recommendations.append(
                "✅ OK: Componente operando dentro dos parâmetros normais."
            )

        return recommendations


class LatencyAnalyzer:
    """Analisador de latência com percentis e heatmaps."""

    def __init__(self, percentiles: Optional[List[float]] = None):
        """
        Inicializa o analisador de latência.

        Args:
            percentiles: Lista de percentis para análise (padrão: [50, 90, 95, 99])
        """
        self.percentiles = percentiles or [50, 90, 95, 99]

    def analyze_latency(self, latency_data: List[float]) -> Dict[str, Any]:
        """
        Analisa dados de latência com percentis e estatísticas.

        Args:
            latency_data: Lista de tempos de latência em milissegundos

        Returns:
            Análise completa de latência
        """
        if not latency_data:
            logger.warning("No latency data provided")
            return {"error": "No data available"}

        logger.info(f"Analyzing {len(latency_data)} latency samples")

        try:
            # Converter para numpy array para eficiência
            latencies = np.array(latency_data)

            # Estatísticas básicas
            stats = {
                "count": len(latencies),
                "mean": float(np.mean(latencies)),
                "median": float(np.median(latencies)),
                "std": float(np.std(latencies)),
                "min": float(np.min(latencies)),
                "max": float(np.max(latencies)),
                "range": float(np.max(latencies) - np.min(latencies)),
            }

            # Percentis
            percentile_values = {}
            for p in self.percentiles:
                percentile_values[f"p{p}"] = float(np.percentile(latencies, p))

            # Outliers detection (usando IQR method)
            q1 = np.percentile(latencies, 25)
            q3 = np.percentile(latencies, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            outliers = latencies[(latencies < lower_bound) | (latencies > upper_bound)]
            outlier_percentage = (len(outliers) / len(latencies)) * 100

            # Heatmap data (para visualização)
            heatmap_data = self._generate_heatmap_data(latencies)

            # Performance classification
            performance_class = self._classify_performance(percentile_values)

            analysis = {
                "statistics": stats,
                "percentiles": percentile_values,
                "outliers": {
                    "count": len(outliers),
                    "percentage": outlier_percentage,
                    "values": outliers.tolist()[:10],  # Top 10 outliers
                },
                "heatmap": heatmap_data,
                "performance_class": performance_class,
                "recommendations": self._generate_latency_recommendations(
                    percentile_values, outlier_percentage
                ),
                "unit": "milliseconds",
                "timestamp": pd.Timestamp.now().isoformat(),
            }

            logger.info(
                f"Latency analysis complete: p95={percentile_values.get('p95', 0):.2f}ms"
            )
            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze latency: {e}")
            return {"error": str(e)}

    def _generate_heatmap_data(self, latencies: np.ndarray) -> Dict[str, Any]:
        """Gera dados para heatmap de latência."""
        try:
            # Criar histograma para heatmap
            hist, bin_edges = np.histogram(latencies, bins=50)

            # Normalizar para 0-1 scale
            if hist.max() > 0:
                normalized_hist = hist / hist.max()
            else:
                normalized_hist = hist

            return {
                "histogram": hist.tolist(),
                "bin_edges": bin_edges.tolist(),
                "normalized": normalized_hist.tolist(),
                "bins": len(bin_edges) - 1,
            }
        except Exception as e:
            logger.error(f"Failed to generate heatmap data: {e}")
            return {"error": str(e)}

    def _classify_performance(self, percentiles: Dict[str, float]) -> str:
        """Classifica performance baseada nos percentis."""
        p95 = percentiles.get("p95", 0)
        p99 = percentiles.get("p99", 0)

        if p95 < 10 and p99 < 20:
            return "EXCELLENT"
        elif p95 < 50 and p99 < 100:
            return "GOOD"
        elif p95 < 200 and p99 < 500:
            return "ACCEPTABLE"
        elif p95 < 1000 and p99 < 2000:
            return "POOR"
        else:
            return "CRITICAL"

    def _generate_latency_recommendations(
        self, percentiles: Dict[str, float], outlier_percentage: float
    ) -> List[str]:
        """Gera recomendações baseadas na análise de latência."""
        recommendations = []

        p95 = percentiles.get("p95", 0)
        p99 = percentiles.get("p99", 0)

        if p95 > 100:
            recommendations.append(
                "🐌 P95 alto (>100ms): Investigate slow queries, "
                "inefficient algorithms, ou resource contention. "
                "Em cloud, review de instance types recomendado."
            )

        if p99 > 500:
            recommendations.append(
                "⚡ P99 muito alto (>500ms): Outliers severos detectados. "
                "Considere caching, connection pooling, ou "
                "async processing para casos extremos."
            )

        if outlier_percentage > 5:
            recommendations.append(
                "📊 Muitos outliers (>5%): Instabilidade detectada. "
                "Investigue garbage collection pauses, "
                "network blips, ou resource starvation."
            )

        if p95 < 10 and p99 < 20:
            recommendations.append(
                "🚀 Excelente performance: Sistema operando com "
                "latência ótima. Continue monitoramento e "
                "establish baseline para futuras comparações."
            )

        return recommendations
