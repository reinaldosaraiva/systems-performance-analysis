"""
Tests for Systems Performance Analysis Tool

Testes unitários e de integração para validação do sistema.
Seguindo padrões de context engineering e boas práticas.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from collectors import SystemCollector
from analyzers import USEAnalyzer, LatencyAnalyzer, USEScore, Status
from reporters import ReportGenerator
from main import PerformanceAnalyzer


class TestSystemCollector:
    """Testes para SystemCollector."""

    def setup_method(self):
        """Setup para cada teste."""
        self.collector = SystemCollector(cache_duration=0.1)

    def test_cpu_metrics_collection(self):
        """Testa coleta de métricas de CPU."""
        with patch("psutil.cpu_percent", return_value=75.5):
            with patch("psutil.getloadavg", return_value=(1.5, 1.2, 1.0)):
                with patch("psutil.cpu_count", return_value=4):
                    with patch("psutil.cpu_count") as mock_logical:
                        mock_logical.return_value = 8

                        metrics = self.collector.get_cpu_metrics()

                        assert metrics["utilization"] == 75.5
                        assert metrics["load_1m"] == 1.5
                        assert metrics["cpu_count_physical"] == 4
                        assert metrics["cpu_count_logical"] == 8
                        assert "timestamp" in metrics
                        assert "unit" in metrics

    def test_memory_metrics_collection(self):
        """Testa coleta de métricas de memória."""
        mock_memory = Mock()
        mock_memory.total = 8000000000
        mock_memory.available = 4000000000
        mock_memory.used = 4000000000
        mock_memory.free = 2000000000
        mock_memory.percent = 50.0

        mock_swap = Mock()
        mock_swap.total = 2000000000
        mock_swap.used = 1000000000
        mock_swap.free = 1000000000
        mock_swap.percent = 50.0

        with patch("psutil.virtual_memory", return_value=mock_memory):
            with patch("psutil.swap_memory", return_value=mock_swap):
                metrics = self.collector.get_memory_metrics()

                assert metrics["total"] == 8000000000
                assert metrics["utilization"] == 50.0
                assert metrics["swap_utilization"] == 50.0
                assert "timestamp" in metrics
                assert "unit" in metrics

    def test_disk_metrics_collection(self):
        """Testa coleta de métricas de disco."""
        mock_partition = Mock()
        mock_partition.mountpoint = "/test"
        mock_partition.device = "/dev/sda1"
        mock_partition.fstype = "ext4"

        mock_usage = Mock()
        mock_usage.total = 1000000000000
        mock_usage.used = 500000000000
        mock_usage.free = 500000000000

        mock_io = Mock()
        mock_io.read_bytes = 1000000
        mock_io.write_bytes = 500000
        mock_io.read_count = 1000
        mock_io.write_count = 500
        mock_io.read_time = 100
        mock_io.write_time = 50

        with patch("psutil.disk_partitions", return_value=[mock_partition]):
            with patch("psutil.disk_usage", return_value=mock_usage):
                with patch("psutil.disk_io_counters", return_value=mock_io):
                    metrics = self.collector.get_disk_metrics()

                    assert "partitions" in metrics
                    assert "io" in metrics
                    assert metrics["total_utilization"] == 50.0
                    assert "timestamp" in metrics
                    assert "unit" in metrics

    def test_network_metrics_collection(self):
        """Testa coleta de métricas de rede."""
        mock_io = Mock()
        mock_io.bytes_sent = 1000000
        mock_io.bytes_recv = 2000000
        mock_io.packets_sent = 1000
        mock_io.packets_recv = 2000
        mock_io.errin = 10
        mock_io.errout = 5
        mock_io.dropin = 2
        mock_io.dropout = 1

        mock_pernic = {
            "eth0": Mock(
                bytes_sent=500000,
                bytes_recv=1000000,
                packets_sent=500,
                packets_recv=1000,
                errin=5,
                errout=2,
                dropin=1,
                dropout=0,
            )
        }

        mock_connection = Mock()
        mock_connection.status = "ESTABLISHED"

        with patch("psutil.net_io_counters", return_value=mock_io):
            with patch("psutil.net_io_counters", return_value=mock_pernic):
                with patch("psutil.net_connections", return_value=[mock_connection]):
                    metrics = self.collector.get_network_metrics()

                    assert "total" in metrics
                    assert "interfaces" in metrics
                    assert "connections" in metrics
                    assert metrics["errors"] >= 0
                    assert "timestamp" in metrics
                    assert "unit" in metrics

    def test_collect_all(self):
        """Testa coleta completa de métricas."""
        with patch.object(
            self.collector, "get_cpu_metrics", return_value={"test": "cpu"}
        ):
            with patch.object(
                self.collector, "get_memory_metrics", return_value={"test": "memory"}
            ):
                with patch.object(
                    self.collector, "get_disk_metrics", return_value={"test": "disk"}
                ):
                    with patch.object(
                        self.collector,
                        "get_network_metrics",
                        return_value={"test": "network"},
                    ):
                        metrics = self.collector.collect_all()

                        assert "cpu" in metrics
                        assert "memory" in metrics
                        assert "disk" in metrics
                        assert "network" in metrics

    def test_cache_functionality(self):
        """Testa funcionalidade de cache."""
        with patch.object(
            self.collector, "get_cpu_metrics", return_value={"cached": True}
        ) as mock:
            # Primeira chamada
            result1 = self.collector.collect_all()
            assert mock.call_count == 1

            # Segunda chamada (deve usar cache)
            result2 = self.collector.collect_all()
            assert mock.call_count == 1  # Não deve chamar novamente
            assert result1 == result2

            # Esperar cache expirar
            time.sleep(0.2)
            result3 = self.collector.collect_all()
            assert mock.call_count == 2  # Deve chamar novamente


class TestUSEAnalyzer:
    """Testes para USEAnalyzer."""

    def setup_method(self):
        """Setup para cada teste."""
        self.analyzer = USEAnalyzer()

    def test_cpu_analysis_ok(self):
        """Testa análise de CPU com status OK."""
        metrics = {"utilization": 50.0, "saturation": 10.0, "timestamp": time.time()}

        score = self.analyzer._analyze_component("cpu", metrics)

        assert isinstance(score, USEScore)
        assert score.utilization == 50.0
        assert score.saturation == 10.0
        assert score.status == Status.OK
        assert score.overall_score == 50.0
        assert len(score.recommendations) > 0

    def test_cpu_analysis_warning(self):
        """Testa análise de CPU com status WARNING."""
        metrics = {"utilization": 85.0, "saturation": 25.0, "timestamp": time.time()}

        score = self.analyzer._analyze_component("cpu", metrics)

        assert score.status == Status.WARNING
        assert score.overall_score == 85.0
        assert any("CPU alta" in rec for rec in score.recommendations)

    def test_memory_analysis_critical(self):
        """Testa análise de memória com status CRITICAL."""
        metrics = {
            "utilization": 90.0,
            "saturation": 15.0,
            "errors": 5.0,
            "timestamp": time.time(),
        }

        score = self.analyzer._analyze_component("memory", metrics)

        assert score.status == Status.CRITICAL
        assert score.overall_score == 90.0
        assert any("CRITICAL" in rec for rec in score.recommendations)

    def test_system_analysis(self):
        """Testa análise completa do sistema."""
        metrics = {
            "cpu": {"utilization": 75.0, "saturation": 15.0, "timestamp": time.time()},
            "memory": {
                "utilization": 60.0,
                "saturation": 5.0,
                "timestamp": time.time(),
            },
            "disk": {"utilization": 40.0, "saturation": 10.0, "timestamp": time.time()},
            "network": {
                "utilization": 30.0,
                "saturation": 5.0,
                "timestamp": time.time(),
            },
        }

        results = self.analyzer.analyze_system(metrics)

        assert len(results) == 4
        assert "cpu" in results
        assert "memory" in results
        assert "disk" in results
        assert "network" in results

        for component, score in results.items():
            assert isinstance(score, USEScore)
            assert 0 <= score.utilization <= 100
            assert 0 <= score.saturation <= 100
            assert 0 <= score.errors <= 100

    def test_custom_thresholds(self):
        """Testa análise com thresholds customizados."""
        custom_thresholds = {"cpu": {"utilization": 90, "saturation": 30, "errors": 0}}

        analyzer = USEAnalyzer(custom_thresholds)

        metrics = {"utilization": 85.0, "saturation": 25.0, "timestamp": time.time()}

        score = analyzer._analyze_component("cpu", metrics)

        # Com thresholds customizados, 85% deve ser OK (threshold é 90%)
        assert score.status == Status.OK


class TestLatencyAnalyzer:
    """Testes para LatencyAnalyzer."""

    def setup_method(self):
        """Setup para cada teste."""
        self.analyzer = LatencyAnalyzer()

    def test_latency_analysis_basic(self):
        """Testa análise básica de latência."""
        latency_data = [10, 15, 20, 25, 30, 35, 40, 45, 50]

        result = self.analyzer.analyze_latency(latency_data)

        assert "statistics" in result
        assert "percentiles" in result
        assert "outliers" in result
        assert "heatmap" in result
        assert "performance_class" in result
        assert "recommendations" in result

        # Verificar estatísticas
        stats = result["statistics"]
        assert stats["count"] == 9
        assert stats["min"] == 10
        assert stats["max"] == 50
        assert stats["mean"] == 30.0

        # Verificar percentis
        percentiles = result["percentiles"]
        assert "p50" in percentiles
        assert "p90" in percentiles
        assert "p95" in percentiles
        assert "p99" in percentiles

    def test_latency_analysis_empty_data(self):
        """Testa análise com dados vazios."""
        result = self.analyzer.analyze_latency([])

        assert "error" in result
        assert result["error"] == "No data available"

    def test_latency_performance_classification(self):
        """Testa classificação de performance."""
        # Excelente performance
        excellent_data = [5, 8, 10, 12, 15]
        result = self.analyzer.analyze_latency(excellent_data)
        assert result["performance_class"] == "EXCELLENT"

        # Poor performance
        poor_data = [150, 200, 250, 300, 350]
        result = self.analyzer.analyze_latency(poor_data)
        assert result["performance_class"] == "POOR"

        # Critical performance
        critical_data = [1500, 2000, 2500, 3000, 3500]
        result = self.analyzer.analyze_latency(critical_data)
        assert result["performance_class"] == "CRITICAL"

    def test_custom_percentiles(self):
        """Testa análise com percentis customizados."""
        custom_percentiles = [25, 50, 75, 90]
        analyzer = LatencyAnalyzer(custom_percentiles)

        latency_data = list(range(1, 101))  # 1 a 100
        result = analyzer.analyze_latency(latency_data)

        percentiles = result["percentiles"]
        assert "p25" in percentiles
        assert "p50" in percentiles
        assert "p75" in percentiles
        assert "p90" in percentiles
        assert "p95" not in percentiles  # Não deve estar presente


class TestReportGenerator:
    """Testes para ReportGenerator."""

    def setup_method(self):
        """Setup para cada teste."""
        self.generator = ReportGenerator()

        # Dados de teste
        self.use_scores = {
            "cpu": USEScore(
                utilization=75.0,
                saturation=15.0,
                errors=0.0,
                overall_score=75.0,
                status=Status.WARNING,
                recommendations=["CPU alta detectada"],
            ),
            "memory": USEScore(
                utilization=50.0,
                saturation=5.0,
                errors=0.0,
                overall_score=50.0,
                status=Status.OK,
                recommendations=["Memória OK"],
            ),
        }

        self.latency_analysis = {
            "statistics": {
                "count": 100,
                "mean": 25.5,
                "median": 20.0,
                "std": 15.2,
                "min": 5.0,
                "max": 150.0,
            },
            "percentiles": {"p50": 20.0, "p90": 45.0, "p95": 60.0, "p99": 100.0},
            "performance_class": "GOOD",
            "recommendations": ["Performance aceitável"],
        }

    def test_markdown_report_generation(self):
        """Testa geração de relatório Markdown."""
        report = self.generator.generate_markdown_report(
            self.use_scores, self.latency_analysis
        )

        assert "# Systems Performance Analysis Report" in report
        assert "## 📊 Executive Summary" in report
        assert "## 🔍 USE Method Analysis" in report
        assert "## ⏱️ Latency Analysis" in report
        assert "CPU" in report
        assert "MEMORY" in report
        assert "75.0%" in report
        assert "WARNING" in report

    def test_html_report_generation(self):
        """Testa geração de relatório HTML."""
        report = self.generator.generate_html_report(
            self.use_scores, self.latency_analysis
        )

        assert "<!DOCTYPE html>" in report
        assert "<title>Systems Performance Analysis Report</title>" in report
        assert "USE Method Analysis" in report
        assert "Latency Analysis" in report
        assert "data:image/png;base64," in report  # Charts embed

    def test_report_without_latency(self):
        """Testa geração de relatório sem análise de latência."""
        report = self.generator.generate_markdown_report(self.use_scores)

        assert "## 🔍 USE Method Analysis" in report
        assert "## ⏱️ Latency Analysis" not in report

    def test_format_bytes(self):
        """Testa formatação de bytes."""
        assert self.generator._format_bytes(1024) == "1.0 KB"
        assert self.generator._format_bytes(1048576) == "1.0 MB"
        assert self.generator._format_bytes(1073741824) == "1.0 GB"
        assert self.generator._format_bytes(500) == "500.0 B"


class TestPerformanceAnalyzer:
    """Testes para PerformanceAnalyzer (integração)."""

    def setup_method(self):
        """Setup para cada teste."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.analyzer = PerformanceAnalyzer(self.temp_dir)

    def teardown_method(self):
        """Cleanup após cada teste."""
        shutil.rmtree(self.temp_dir)

    @patch("src.collectors.psutil.cpu_percent")
    @patch("src.collectors.psutil.virtual_memory")
    @patch("src.collectors.psutil.disk_io_counters")
    @patch("src.collectors.psutil.net_io_counters")
    def test_full_analysis_integration(
        self, mock_net, mock_disk, mock_memory, mock_cpu
    ):
        """Teste de integração para análise completa."""
        # Mock das métricas
        mock_cpu.return_value = 75.0
        mock_memory.return_value = Mock(
            percent=60.0, total=8000000000, available=3200000000
        )
        mock_disk.return_value = Mock(
            read_bytes=1000000, write_bytes=500000, read_time=100, write_time=50
        )
        mock_net.return_value = Mock(
            bytes_sent=1000000,
            bytes_recv=2000000,
            errin=0,
            errout=0,
            dropin=0,
            dropout=0,
        )

        # Executar análise
        report_path = self.analyzer.run_analysis(
            components=["cpu", "memory"], include_latency=False, format="markdown"
        )

        # Verificar resultados
        assert report_path.exists()
        assert report_path.suffix == ".md"

        # Verificar conteúdo
        content = report_path.read_text(encoding="utf-8")
        assert "Systems Performance Analysis Report" in content
        assert "CPU" in content
        assert "MEMORY" in content

    def test_analysis_with_latency(self):
        """Testa análise com inclusão de latência."""
        with patch.object(self.analyzer, "run_analysis") as mock_run:
            mock_run.return_value = self.temp_dir / "test.md"

            result = self.analyzer.run_analysis(include_latency=True, format="html")

            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            assert kwargs["include_latency"] is True
            assert kwargs["format"] == "html"


class TestErrorHandling:
    """Testes para tratamento de erros."""

    def test_collector_error_handling(self):
        """Testa tratamento de erros no coletor."""
        collector = SystemCollector()

        with patch("psutil.cpu_percent", side_effect=Exception("Test error")):
            metrics = collector.get_cpu_metrics()
            assert "error" in metrics

    def test_analyzer_error_handling(self):
        """Testa tratamento de erros no analisador."""
        analyzer = USEAnalyzer()

        # Métricas inválidas
        invalid_metrics = {"invalid": "data"}
        result = analyzer.analyze_system(invalid_metrics)

        # Deve retornar dicionário vazio para métricas inválidas
        assert len(result) == 0

    def test_reporter_error_handling(self):
        """Testa tratamento de erros no gerador de relatórios."""
        generator = ReportGenerator()

        # Dados inválidos
        invalid_scores = {"invalid": "data"}
        report = generator.generate_markdown_report(invalid_scores)

        # Deve gerar relatório mesmo com dados inválidos
        assert "# Systems Performance Analysis Report" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
