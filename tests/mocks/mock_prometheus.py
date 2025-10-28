"""
Mock Prometheus Server para Testes
Simula métricas do Node Exporter para testar o analisador
"""

import json
import time
import random
from datetime import datetime
from typing import Dict, Any
from aiohttp import web, ClientSession
import asyncio


class MockPrometheus:
    """Servidor Prometheus mock para testes."""

    def __init__(self, port: int = 9090):
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        self.start_time = time.time()

    def setup_routes(self):
        """Configura rotas da API Prometheus."""
        self.app.router.add_get("/api/v1/query_range", self.handle_query_range)
        self.app.router.add_get("/api/v1/query", self.handle_query)
        self.app.router.add_get("/api/v1/targets", self.handle_targets)
        self.app.router.add_get("/", self.handle_root)

    async def handle_root(self, request):
        """Root endpoint."""
        return web.json_response(
            {"status": "success", "data": {"version": "2.47.2", "revision": "mock"}}
        )

    async def handle_targets(self, request):
        """Targets endpoint."""
        return web.json_response(
            {
                "status": "success",
                "data": {
                    "activeTargets": [
                        {
                            "labels": {"job": "node_exporter"},
                            "health": "up",
                            "lastScrape": datetime.now().isoformat(),
                            "lastError": "",
                        }
                    ]
                },
            }
        )

    def generate_cpu_metrics(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera métricas de CPU mock."""
        if "cpu_utilization" in query:
            # Simula CPU utilization variando entre 20-80%
            values = []
            current_time = start_time
            while current_time <= end_time:
                cpu_util = 30 + random.random() * 40  # 30-70%
                values.append([int(current_time * 1000), str(cpu_util)])
                current_time += step

            return {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {
                            "__name__": "cpu_utilization",
                            "instance": "localhost:9100",
                        },
                        "values": values,
                    }
                ],
            }

        elif "node_load1" in query:
            # Simula load average
            values = []
            current_time = start_time
            base_load = 2.0 + random.random() * 4.0  # 2-6
            while current_time <= end_time:
                load = base_load + random.random() * 0.5
                values.append([int(current_time * 1000), str(load)])
                current_time += step

            return {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {
                            "__name__": "node_load1",
                            "instance": "localhost:9100",
                        },
                        "values": values,
                    }
                ],
            }

        elif "node_cpu_seconds_total" in query:
            # Simula CPU count
            return {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {
                            "__name__": "node_cpu_seconds_total",
                            "mode": "idle",
                            "instance": "localhost:9100",
                        },
                        "value": [
                            int(time.time() * 1000),
                            str(1000000 + random.random() * 100000),
                        ],
                    }
                ]
                * 8,  # 8 CPUs
            }

        return {"resultType": "matrix", "result": []}

    def generate_memory_metrics(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera métricas de memória mock."""
        if "node_memory_MemTotal_bytes" in query:
            return {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {
                            "__name__": "node_memory_MemTotal_bytes",
                            "instance": "localhost:9100",
                        },
                        "value": [
                            int(time.time() * 1000),
                            str(16 * 1024 * 1024 * 1024),
                        ],  # 16GB
                    }
                ],
            }

        elif "node_memory_MemAvailable_bytes" in query:
            values = []
            current_time = start_time
            base_available = 4 * 1024 * 1024 * 1024  # 4GB base
            while current_time <= end_time:
                available = base_available + random.random() * 2 * 1024 * 1024 * 1024
                values.append([int(current_time * 1000), str(available)])
                current_time += step

            return {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {
                            "__name__": "node_memory_MemAvailable_bytes",
                            "instance": "localhost:9100",
                        },
                        "values": values,
                    }
                ],
            }

        elif "node_memory_SwapTotal_bytes" in query:
            return {
                "resultType": "vector",
                "result": [
                    {
                        "metric": {
                            "__name__": "node_memory_SwapTotal_bytes",
                            "instance": "localhost:9100",
                        },
                        "value": [
                            int(time.time() * 1000),
                            str(8 * 1024 * 1024 * 1024),
                        ],  # 8GB
                    }
                ],
            }

        elif "node_memory_SwapFree_bytes" in query:
            values = []
            current_time = start_time
            base_free = 2 * 1024 * 1024 * 1024  # 2GB base
            while current_time <= end_time:
                free = base_free + random.random() * 1024 * 1024 * 1024
                values.append([int(current_time * 1000), str(free)])
                current_time += step

            return {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {
                            "__name__": "node_memory_SwapFree_bytes",
                            "instance": "localhost:9100",
                        },
                        "values": values,
                    }
                ],
            }

        return {"resultType": "matrix", "result": []}

    def generate_disk_metrics(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera métricas de disco mock."""
        if "node_disk_read_bytes_total" in query:
            values = []
            current_time = start_time
            base_read = 50 * 1024 * 1024  # 50MB/s base
            while current_time <= end_time:
                read_rate = (
                    base_read + random.random() * 100 * 1024 * 1024
                )  # +100MB/s variation
                values.append([int(current_time * 1000), str(read_rate)])
                current_time += step

            return {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {
                            "__name__": "node_disk_read_bytes_total",
                            "device": "sda",
                            "instance": "localhost:9100",
                        },
                        "values": values,
                    }
                ],
            }

        elif "node_disk_write_bytes_total" in query:
            values = []
            current_time = start_time
            base_write = 30 * 1024 * 1024  # 30MB/s base
            while current_time <= end_time:
                write_rate = (
                    base_write + random.random() * 50 * 1024 * 1024
                )  # +50MB/s variation
                values.append([int(current_time * 1000), str(write_rate)])
                current_time += step

            return {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {
                            "__name__": "node_disk_write_bytes_total",
                            "device": "sda",
                            "instance": "localhost:9100",
                        },
                        "values": values,
                    }
                ],
            }

        elif "node_disk_io_time_seconds_total" in query:
            values = []
            current_time = start_time
            while current_time <= end_time:
                io_time = random.random() * 0.1  # 0-100ms
                values.append([int(current_time * 1000), str(io_time)])
                current_time += step

            return {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {
                            "__name__": "node_disk_io_time_seconds_total",
                            "device": "sda",
                            "instance": "localhost:9100",
                        },
                        "values": values,
                    }
                ],
            }

        return {"resultType": "matrix", "result": []}

    def generate_network_metrics(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera métricas de rede mock."""
        if "node_network_receive_bytes_total" in query:
            values = []
            current_time = start_time
            base_rx = 10 * 1024 * 1024  # 10MB/s base
            while current_time <= end_time:
                rx_rate = (
                    base_rx + random.random() * 50 * 1024 * 1024
                )  # +50MB/s variation
                values.append([int(current_time * 1000), str(rx_rate)])
                current_time += step

            return {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {
                            "__name__": "node_network_receive_bytes_total",
                            "device": "eth0",
                            "instance": "localhost:9100",
                        },
                        "values": values,
                    }
                ],
            }

        elif "node_network_transmit_bytes_total" in query:
            values = []
            current_time = start_time
            base_tx = 5 * 1024 * 1024  # 5MB/s base
            while current_time <= end_time:
                tx_rate = (
                    base_tx + random.random() * 20 * 1024 * 1024
                )  # +20MB/s variation
                values.append([int(current_time * 1000), str(tx_rate)])
                current_time += step

            return {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {
                            "__name__": "node_network_transmit_bytes_total",
                            "device": "eth0",
                            "instance": "localhost:9100",
                        },
                        "values": values,
                    }
                ],
            }

        return {"resultType": "matrix", "result": []}

    def generate_cpu_utilization(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera CPU utilization (100 - avg idle)."""
        values = []
        current_time = start_time
        while current_time <= end_time:
            cpu_util = 30 + random.random() * 40  # 30-70%
            values.append([int(current_time * 1000), str(cpu_util)])
            current_time += step

        return {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": "cpu_utilization",
                        "instance": "localhost:9100",
                    },
                    "values": values,
                }
            ],
        }

    def generate_load_metrics(
        self, period: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera load average metrics."""
        values = []
        current_time = start_time
        base_load = {"1": 2.0, "5": 1.8, "15": 1.5}[period] + random.random() * 2.0
        while current_time <= end_time:
            load = base_load + random.random() * 0.5
            values.append([int(current_time * 1000), str(load)])
            current_time += step

        return {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": f"node_load{period}",
                        "instance": "localhost:9100",
                    },
                    "values": values,
                }
            ],
        }

    def generate_cpu_count(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera CPU count."""
        values = []
        current_time = start_time
        while current_time <= end_time:
            values.append(
                [int(current_time * 1000), str(1000000 + random.random() * 100000)]
            )
            current_time += step

        return {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": "node_cpu_seconds_total",
                        "mode": "idle",
                        "instance": "localhost:9100",
                    },
                    "values": values,
                }
            ]
            * 8,  # 8 CPUs
        }

    def generate_memory_total(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera memória total."""
        values = []
        current_time = start_time
        while current_time <= end_time:
            values.append([int(current_time * 1000), str(16 * 1024 * 1024 * 1024)])
            current_time += step

        return {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": "node_memory_MemTotal_bytes",
                        "instance": "localhost:9100",
                    },
                    "values": values,
                }
            ],
        }

    def generate_memory_available(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera memória disponível."""
        values = []
        current_time = start_time
        base_available = 4 * 1024 * 1024 * 1024  # 4GB base
        while current_time <= end_time:
            available = base_available + random.random() * 2 * 1024 * 1024 * 1024
            values.append([int(current_time * 1000), str(available)])
            current_time += step

        return {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": "node_memory_MemAvailable_bytes",
                        "instance": "localhost:9100",
                    },
                    "values": values,
                }
            ],
        }

    def generate_swap_total(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera swap total."""
        values = []
        current_time = start_time
        while current_time <= end_time:
            values.append([int(current_time * 1000), str(8 * 1024 * 1024 * 1024)])
            current_time += step

        return {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": "node_memory_SwapTotal_bytes",
                        "instance": "localhost:9100",
                    },
                    "values": values,
                }
            ],
        }

    def generate_swap_free(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera swap livre."""
        values = []
        current_time = start_time
        base_free = 2 * 1024 * 1024 * 1024  # 2GB base
        while current_time <= end_time:
            free = base_free + random.random() * 1024 * 1024 * 1024
            values.append([int(current_time * 1000), str(free)])
            current_time += step

        return {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": "node_memory_SwapFree_bytes",
                        "instance": "localhost:9100",
                    },
                    "values": values,
                }
            ],
        }

    def generate_disk_read(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera taxa de leitura do disco (bytes/sec)."""
        values = []
        current_time = start_time
        base_rate = 50 * 1024 * 1024  # 50MB/s
        while current_time <= end_time:
            rate = base_rate + random.random() * 100 * 1024 * 1024
            values.append([int(current_time * 1000), str(rate)])
            current_time += step

        return {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": "node_disk_read_bytes_total",
                        "device": "sda",
                        "instance": "localhost:9100",
                    },
                    "values": values,
                }
            ],
        }

    def generate_disk_write(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera taxa de escrita do disco (bytes/sec)."""
        values = []
        current_time = start_time
        base_rate = 30 * 1024 * 1024  # 30MB/s
        while current_time <= end_time:
            rate = base_rate + random.random() * 50 * 1024 * 1024
            values.append([int(current_time * 1000), str(rate)])
            current_time += step

        return {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": "node_disk_write_bytes_total",
                        "device": "sda",
                        "instance": "localhost:9100",
                    },
                    "values": values,
                }
            ],
        }

    def generate_disk_reads(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera número de operações de leitura (ops/sec)."""
        values = []
        current_time = start_time
        base_ops = 100  # 100 ops/s
        while current_time <= end_time:
            ops = base_ops + random.random() * 200
            values.append([int(current_time * 1000), str(ops)])
            current_time += step

        return {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": "node_disk_reads_completed_total",
                        "device": "sda",
                        "instance": "localhost:9100",
                    },
                    "values": values,
                }
            ],
        }

    def generate_disk_writes(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera número de operações de escrita (ops/sec)."""
        values = []
        current_time = start_time
        base_ops = 80  # 80 ops/s
        while current_time <= end_time:
            ops = base_ops + random.random() * 150
            values.append([int(current_time * 1000), str(ops)])
            current_time += step

        return {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": "node_disk_writes_completed_total",
                        "device": "sda",
                        "instance": "localhost:9100",
                    },
                    "values": values,
                }
            ],
        }

    def generate_disk_io_time(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera tempo de I/O do disco (percent)."""
        values = []
        current_time = start_time
        while current_time <= end_time:
            io_time = random.random() * 20  # 0-20%
            values.append([int(current_time * 1000), str(io_time)])
            current_time += step

        return {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": "node_disk_io_time_seconds_total",
                        "device": "sda",
                        "instance": "localhost:9100",
                    },
                    "values": values,
                }
            ],
        }

    def generate_network_receive(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera taxa de recebimento de rede (bytes/sec)."""
        values = []
        current_time = start_time
        base_rate = 10 * 1024 * 1024  # 10MB/s
        while current_time <= end_time:
            rate = base_rate + random.random() * 50 * 1024 * 1024
            values.append([int(current_time * 1000), str(rate)])
            current_time += step

        return {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": "node_network_receive_bytes_total",
                        "device": "eth0",
                        "instance": "localhost:9100",
                    },
                    "values": values,
                }
            ],
        }

    def generate_network_transmit(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera taxa de transmissão de rede (bytes/sec)."""
        values = []
        current_time = start_time
        base_rate = 5 * 1024 * 1024  # 5MB/s
        while current_time <= end_time:
            rate = base_rate + random.random() * 20 * 1024 * 1024
            values.append([int(current_time * 1000), str(rate)])
            current_time += step

        return {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": "node_network_transmit_bytes_total",
                        "device": "eth0",
                        "instance": "localhost:9100",
                    },
                    "values": values,
                }
            ],
        }

    def generate_network_receive_packets(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera pacotes recebidos (packets/sec)."""
        values = []
        current_time = start_time
        base_rate = 1000  # 1000 packets/s
        while current_time <= end_time:
            rate = base_rate + random.random() * 5000
            values.append([int(current_time * 1000), str(rate)])
            current_time += step

        return {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": "node_network_receive_packets_total",
                        "device": "eth0",
                        "instance": "localhost:9100",
                    },
                    "values": values,
                }
            ],
        }

    def generate_network_transmit_packets(
        self, query: str, start_time: float, end_time: float, step: int
    ) -> Dict[str, Any]:
        """Gera pacotes transmitidos (packets/sec)."""
        values = []
        current_time = start_time
        base_rate = 800  # 800 packets/s
        while current_time <= end_time:
            rate = base_rate + random.random() * 3000
            values.append([int(current_time * 1000), str(rate)])
            current_time += step

        return {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {
                        "__name__": "node_network_transmit_packets_total",
                        "device": "eth0",
                        "instance": "localhost:9100",
                    },
                    "values": values,
                }
            ],
        }

    async def handle_query_range(self, request):
        """Handle query_range API."""
        params = request.query
        query = params.get("query", "")

        # Parse timestamps - Prometheus envia como ISO 8601
        start_str = params.get("start", str(time.time() - 300))
        end_str = params.get("end", str(time.time()))

        try:
            # Try parsing as ISO format first
            from datetime import datetime

            start = datetime.fromisoformat(start_str.replace("Z", "+00:00")).timestamp()
            end = datetime.fromisoformat(end_str.replace("Z", "+00:00")).timestamp()
        except:
            # Fallback to float
            start = float(start_str)
            end = float(end_str)

        step = int(params.get("step", "300").replace("s", ""))

        # Gera métricas baseado na query específica
        if "node_cpu_seconds_total" in query and "idle" in query:
            result = self.generate_cpu_utilization(query, start, end, step)
        elif "node_load1" in query:
            result = self.generate_load_metrics("1", start, end, step)
        elif "node_load5" in query:
            result = self.generate_load_metrics("5", start, end, step)
        elif "node_load15" in query:
            result = self.generate_load_metrics("15", start, end, step)
        elif "node_cpu_seconds_total" in query:
            result = self.generate_cpu_count(query, start, end, step)
        elif "node_memory_MemTotal_bytes" in query:
            result = self.generate_memory_total(query, start, end, step)
        elif "node_memory_MemAvailable_bytes" in query:
            result = self.generate_memory_available(query, start, end, step)
        elif "node_memory_SwapTotal_bytes" in query:
            result = self.generate_swap_total(query, start, end, step)
        elif "node_memory_SwapFree_bytes" in query:
            result = self.generate_swap_free(query, start, end, step)
        elif "node_disk_read_bytes_total" in query:
            result = self.generate_disk_read(query, start, end, step)
        elif "node_disk_write_bytes_total" in query:
            result = self.generate_disk_write(query, start, end, step)
        elif "node_disk_reads_completed_total" in query:
            result = self.generate_disk_reads(query, start, end, step)
        elif "node_disk_writes_completed_total" in query:
            result = self.generate_disk_writes(query, start, end, step)
        elif "node_disk_io_time_seconds_total" in query:
            result = self.generate_disk_io_time(query, start, end, step)
        elif "node_network_receive_bytes_total" in query:
            result = self.generate_network_receive(query, start, end, step)
        elif "node_network_transmit_bytes_total" in query:
            result = self.generate_network_transmit(query, start, end, step)
        elif "node_network_receive_packets_total" in query:
            result = self.generate_network_receive_packets(query, start, end, step)
        elif "node_network_transmit_packets_total" in query:
            result = self.generate_network_transmit_packets(query, start, end, step)
        else:
            result = {"resultType": "matrix", "result": []}

        return web.json_response({"status": "success", "data": result})

    async def handle_query(self, request):
        """Handle instant query API."""
        params = request.query
        query = params.get("query", "")

        # Para queries instantes, retorna valor atual
        if "up" in query:
            return web.json_response(
                {
                    "status": "success",
                    "data": {
                        "resultType": "vector",
                        "result": [
                            {
                                "metric": {"__name__": "up", "job": "node_exporter"},
                                "value": [int(time.time() * 1000), "1"],
                            }
                        ],
                    },
                }
            )

        return web.json_response(
            {"status": "success", "data": {"resultType": "vector", "result": []}}
        )

    async def start(self):
        """Inicia o servidor mock."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", self.port)
        await site.start()
        print(f"🚀 Mock Prometheus server started on http://localhost:{self.port}")
        print(
            f"📊 Metrics available at: http://localhost:{self.port}/api/v1/query_range"
        )
        print(f"🎯 Targets at: http://localhost:{self.port}/api/v1/targets")


async def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(description="Mock Prometheus Server for Testing")
    parser.add_argument("--port", type=int, default=9090, help="Port to bind to")
    parser.add_argument(
        "--duration", type=int, default=60, help="Duration to run (seconds)"
    )

    args = parser.parse_args()

    mock_prometheus = MockPrometheus(args.port)
    await mock_prometheus.start()

    try:
        await asyncio.sleep(args.duration)
    except KeyboardInterrupt:
        print("\n🛑 Mock Prometheus stopped by user")


if __name__ == "__main__":
    asyncio.run(main())
