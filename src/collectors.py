"""
System Metrics Collectors

Coleta de métricas do sistema usando psutil e /proc filesystem.
Seguindo padrões de context engineering e regras do CLAUDE.md.
"""

import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path

import psutil

logger = logging.getLogger(__name__)


class SystemCollector:
    """Coletor de métricas do sistema com tratamento de erro e unidades."""

    def __init__(self, cache_duration: float = 1.0):
        """
        Inicializa o coletor de métricas.

        Args:
            cache_duration: Duração do cache em segundos para evitar chamadas excessivas
        """
        self.cache_duration = cache_duration
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_update: float = 0

    def collect_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Coleta todas as métricas do sistema.

        Returns:
            Dicionário com métricas de CPU, memory, disk e network
        """
        current_time = time.time()

        # Usar cache se ainda válido
        if current_time - self._last_update < self.cache_duration and self._cache:
            logger.debug("Using cached metrics")
            return self._cache

        logger.info("Collecting system metrics")
        metrics = {}

        try:
            metrics["cpu"] = self.get_cpu_metrics()
            metrics["memory"] = self.get_memory_metrics()
            metrics["disk"] = self.get_disk_metrics()
            metrics["network"] = self.get_network_metrics()

            # Atualizar cache
            self._cache = metrics
            self._last_update = current_time

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            raise

        return metrics

    def get_cpu_metrics(self) -> Dict[str, Any]:
        """
        Coleta métricas de CPU.

        Returns:
            Métricas de CPU com unidades e timestamps
        """
        try:
            # CPU utilization (percent)
            cpu_percent = psutil.cpu_percent(interval=1)

            # Load averages (Linux/Unix only)
            try:
                load_avg = psutil.getloadavg()
                load_1m, load_5m, load_15m = load_avg
            except AttributeError:
                # Windows não tem load averages
                load_1m = load_5m = load_15m = 0

            # CPU count
            cpu_count = psutil.cpu_count() or 1
            cpu_count_logical = psutil.cpu_count(logical=True) or 1

            # CPU times
            cpu_times = psutil.cpu_times()

            # Context switches (Linux only)
            context_switches = 0
            try:
                with open("/proc/stat", "r") as f:
                    for line in f:
                        if line.startswith("ctxt"):
                            context_switches = int(line.split()[1])
                            break
            except (FileNotFoundError, PermissionError):
                logger.debug("Could not read context switches from /proc/stat")

            metrics = {
                "utilization": cpu_percent,  # (%)
                "load_1m": load_1m,
                "load_5m": load_5m,
                "load_15m": load_15m,
                "cpu_count_physical": cpu_count,
                "cpu_count_logical": cpu_count_logical,
                "cpu_times_user": cpu_times.user,  # (seconds)
                "cpu_times_system": cpu_times.system,  # (seconds)
                "cpu_times_idle": cpu_times.idle,  # (seconds)
                "context_switches": context_switches,
                "saturation": (load_1m / cpu_count) * 100
                if cpu_count > 0
                else 0,  # (%)
                "timestamp": time.time(),
                "unit": {
                    "utilization": "%",
                    "load": "processes",
                    "cpu_times": "seconds",
                    "context_switches": "count",
                    "saturation": "%",
                },
            }

            logger.debug(f"CPU metrics collected: utilization={cpu_percent:.1f}%")
            return metrics

        except Exception as e:
            logger.error(f"Failed to collect CPU metrics: {e}")
            return {"error": str(e), "timestamp": time.time()}

    def get_memory_metrics(self) -> Dict[str, Any]:
        """
        Coleta métricas de memória.

        Returns:
            Métricas de memória com unidades
        """
        try:
            # Virtual memory
            virtual_mem = psutil.virtual_memory()

            # Swap memory
            swap_mem = psutil.swap_memory()

            # Memory pressure indicators
            memory_pressure = 0
            try:
                # Linux memory pressure
                with open("/proc/pressure/memory", "r") as f:
                    for line in f:
                        if line.startswith("some"):
                            parts = line.split()
                            for part in parts:
                                if part.startswith("avg60="):
                                    memory_pressure = float(part.split("=")[1])
                                    break
            except (FileNotFoundError, PermissionError):
                logger.debug(
                    "Could not read memory pressure from /proc/pressure/memory"
                )

            metrics = {
                "total": virtual_mem.total,  # (bytes)
                "available": virtual_mem.available,  # (bytes)
                "used": virtual_mem.used,  # (bytes)
                "free": virtual_mem.free,  # (bytes)
                "utilization": virtual_mem.percent,  # (%)
                "buffers": getattr(virtual_mem, "buffers", 0),  # (bytes)
                "cached": getattr(virtual_mem, "cached", 0),  # (bytes)
                "swap_total": swap_mem.total,  # (bytes)
                "swap_used": swap_mem.used,  # (bytes)
                "swap_free": swap_mem.free,  # (bytes)
                "swap_utilization": swap_mem.percent,  # (%)
                "memory_pressure": memory_pressure,
                "saturation": memory_pressure * 10,  # Convert to percentage-like scale
                "timestamp": time.time(),
                "unit": {
                    "memory": "bytes",
                    "utilization": "%",
                    "pressure": "percentage",
                    "saturation": "%",
                },
            }

            logger.debug(
                f"Memory metrics collected: utilization={virtual_mem.percent:.1f}%"
            )
            return metrics

        except Exception as e:
            logger.error(f"Failed to collect memory metrics: {e}")
            return {"error": str(e), "timestamp": time.time()}

    def get_disk_metrics(self) -> Dict[str, Any]:
        """
        Coleta métricas de disco.

        Returns:
            Métricas de disco com unidades
        """
        try:
            disk_metrics = {}

            # Disk usage for all mounted partitions
            partitions = psutil.disk_partitions()
            total_usage = 0
            total_free = 0
            total_size = 0

            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    total_size += usage.total
                    total_free += usage.free
                    total_usage += usage.used

                    disk_metrics[f"partition_{partition.device.replace('/', '_')}"] = {
                        "total": usage.total,  # (bytes)
                        "used": usage.used,  # (bytes)
                        "free": usage.free,  # (bytes)
                        "utilization": (usage.used / usage.total) * 100
                        if usage.total > 0
                        else 0,  # (%)
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                    }
                except PermissionError:
                    logger.debug(
                        f"Permission denied for partition {partition.mountpoint}"
                    )
                    continue

            # Disk I/O statistics
            disk_io = psutil.disk_io_counters()
            io_metrics = {}
            if disk_io:
                io_metrics = {
                    "read_count": disk_io.read_count,  # (operations)
                    "write_count": disk_io.write_count,  # (operations)
                    "read_bytes": disk_io.read_bytes,  # (bytes)
                    "write_bytes": disk_io.write_bytes,  # (bytes)
                    "read_time": disk_io.read_time,  # (milliseconds)
                    "write_time": disk_io.write_time,  # (milliseconds)
                    "read_throughput": disk_io.read_bytes / 1024 / 1024,  # (MB/s)
                    "write_throughput": disk_io.write_bytes / 1024 / 1024,  # (MB/s)
                    "utilization": ((disk_io.read_time + disk_io.write_time) / 10)
                    if (disk_io.read_time + disk_io.write_time) > 0
                    else 0,  # (%)
                }

            # Combine metrics
            metrics = {
                "partitions": disk_metrics,
                "io": io_metrics,
                "total_size": total_size,  # (bytes)
                "total_used": total_usage,  # (bytes)
                "total_free": total_free,  # (bytes)
                "total_utilization": (total_usage / total_size) * 100
                if total_size > 0
                else 0,  # (%)
                "saturation": io_metrics.get("utilization", 0),  # (%)
                "timestamp": time.time(),
                "unit": {
                    "size": "bytes",
                    "throughput": "MB/s",
                    "utilization": "%",
                    "time": "milliseconds",
                    "count": "operations",
                },
            }

            logger.debug(
                f"Disk metrics collected: utilization={metrics['total_utilization']:.1f}%"
            )
            return metrics

        except Exception as e:
            logger.error(f"Failed to collect disk metrics: {e}")
            return {"error": str(e), "timestamp": time.time()}

    def get_network_metrics(self) -> Dict[str, Any]:
        """
        Coleta métricas de rede.

        Returns:
            Métricas de rede com unidades
        """
        try:
            network_metrics = {}

            # Network I/O statistics
            net_io = psutil.net_io_counters()
            total_metrics = {}
            if net_io:
                total_metrics = {
                    "bytes_sent": net_io.bytes_sent,  # (bytes)
                    "bytes_recv": net_io.bytes_recv,  # (bytes)
                    "packets_sent": net_io.packets_sent,  # (packets)
                    "packets_recv": net_io.packets_recv,  # (packets)
                    "errin": net_io.errin,  # (errors)
                    "errout": net_io.errout,  # (errors)
                    "dropin": net_io.dropin,  # (packets)
                    "dropout": net_io.dropout,  # (packets)
                    "error_rate": (
                        (net_io.errin + net_io.errout)
                        / (net_io.packets_sent + net_io.packets_recv)
                    )
                    * 100
                    if (net_io.packets_sent + net_io.packets_recv) > 0
                    else 0,  # (%)
                    "drop_rate": (
                        (net_io.dropin + net_io.dropout)
                        / (net_io.packets_sent + net_io.packets_recv)
                    )
                    * 100
                    if (net_io.packets_sent + net_io.packets_recv) > 0
                    else 0,  # (%)
                }

            # Per-interface statistics
            net_io_pernic = psutil.net_io_counters(pernic=True)
            interface_metrics = {}

            for interface, stats in net_io_pernic.items():
                # Skip loopback interfaces
                if interface.startswith("lo"):
                    continue

                interface_metrics[interface] = {
                    "bytes_sent": stats.bytes_sent,  # (bytes)
                    "bytes_recv": stats.bytes_recv,  # (bytes)
                    "packets_sent": stats.packets_sent,  # (packets)
                    "packets_recv": stats.packets_recv,  # (packets)
                    "errin": stats.errin,  # (errors)
                    "errout": stats.errout,  # (errors)
                    "dropin": stats.dropin,  # (packets)
                    "dropout": stats.dropout,  # (packets)
                }

            # Network connections
            connections = psutil.net_connections()
            connection_stats = {
                "established": len(
                    [c for c in connections if c.status == "ESTABLISHED"]
                ),
                "listen": len([c for c in connections if c.status == "LISTEN"]),
                "time_wait": len([c for c in connections if c.status == "TIME_WAIT"]),
                "total": len(connections),
            }

            metrics = {
                "total": total_metrics,
                "interfaces": interface_metrics,
                "connections": connection_stats,
                "saturation": total_metrics.get("drop_rate", 0),  # (%)
                "errors": total_metrics.get("error_rate", 0),  # (%)
                "timestamp": time.time(),
                "unit": {
                    "bytes": "bytes",
                    "packets": "count",
                    "errors": "count",
                    "rate": "%",
                    "connections": "count",
                },
            }

            logger.debug(
                f"Network metrics collected: error_rate={total_metrics.get('error_rate', 0):.2f}%"
            )
            return metrics

        except Exception as e:
            logger.error(f"Failed to collect network metrics: {e}")
            return {"error": str(e), "timestamp": time.time()}

    def get_safe_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Coleta métricas de forma segura, fallback para métodos alternativos se necessário.

        Returns:
            Métricas com fallback para valores seguros
        """
        try:
            return self.collect_all()
        except Exception as e:
            logger.warning(f"Full collection failed, using safe metrics: {e}")

            safe_metrics = {}
            try:
                safe_metrics["cpu"] = {
                    "utilization": psutil.cpu_percent(interval=0.1),
                    "timestamp": time.time(),
                    "unit": {"utilization": "%"},
                }
            except:
                safe_metrics["cpu"] = {
                    "error": "CPU metrics unavailable",
                    "timestamp": time.time(),
                }

            try:
                mem = psutil.virtual_memory()
                safe_metrics["memory"] = {
                    "utilization": mem.percent,
                    "timestamp": time.time(),
                    "unit": {"utilization": "%"},
                }
            except:
                safe_metrics["memory"] = {
                    "error": "Memory metrics unavailable",
                    "timestamp": time.time(),
                }

            return safe_metrics
