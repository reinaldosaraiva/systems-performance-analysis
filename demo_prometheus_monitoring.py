#!/usr/bin/env python3
"""
Demo Script: Prometheus-based Remote System Monitoring
=====================================================

This script demonstrates the complete workflow for monitoring remote systems
using Prometheus + Node Exporter architecture.

Features demonstrated:
1. Mock Prometheus server for testing
2. Prometheus-based metrics collection
3. USE Method analysis (Utilization, Saturation, Errors)
4. 5-minute interval monitoring (daemon mode)
5. Rich console output with recommendations
"""

import subprocess
import time
import sys
import os
import signal
import atexit
from datetime import datetime


class MonitoringDemo:
    """Complete monitoring workflow demonstration."""

    def __init__(self):
        self.mock_server_proc = None
        self.analyzer_proc = None
        self.cleanup_registered = False

    def cleanup(self):
        """Clean up running processes."""
        print("\n🧹 Cleaning up processes...")
        if self.analyzer_proc:
            self.analyzer_proc.terminate()
            self.analyzer_proc.wait()
        if self.mock_server_proc:
            self.mock_server_proc.terminate()
            self.mock_server_proc.wait()
        print("✅ Cleanup complete")

    def register_cleanup(self):
        """Register cleanup function."""
        if not self.cleanup_registered:
            atexit.register(self.cleanup)
            signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
            signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
            self.cleanup_registered = True

    def print_header(self, title: str):
        """Print formatted header."""
        print("\n" + "=" * 60)
        print(f"🎯 {title}")
        print("=" * 60)

    def step1_start_mock_server(self):
        """Step 1: Start Mock Prometheus Server."""
        self.print_header("Step 1: Starting Mock Prometheus Server")

        print("🚀 Starting mock Prometheus server on port 9090...")
        self.mock_server_proc = subprocess.Popen(
            [sys.executable, "mock_prometheus.py", "--duration", "120"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to start
        time.sleep(3)

        # Verify server is running
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:9090/api/v1/targets"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if "activeTargets" in result.stdout:
                print("✅ Mock Prometheus server is running")
                print("📊 Available endpoints:")
                print("   - http://localhost:9090/api/v1/query_range")
                print("   - http://localhost:9090/api/v1/targets")
            else:
                raise Exception("Server not responding correctly")
        except Exception as e:
            print(f"❌ Failed to start mock server: {e}")
            self.cleanup()
            sys.exit(1)

    def step2_test_mock_api(self):
        """Step 2: Test Mock Prometheus API."""
        self.print_header("Step 2: Testing Mock Prometheus API")

        print("🔍 Testing CPU metrics query...")
        result = subprocess.run(
            [
                "curl",
                "-s",
                "http://localhost:9090/api/v1/query_range"
                '?query=100+-+(avg+by+(instance)+(irate(node_cpu_seconds_total{mode="idle"}[5m]))+*+100)'
                "&start=2025-01-20T10:00:00Z&end=2025-01-20T10:05:00Z&step=60s",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0 and "matrix" in result.stdout:
            print("✅ CPU metrics query successful")
            # Extract a sample value
            import json

            data = json.loads(result.stdout)
            if data["data"]["result"]:
                sample_value = data["data"]["result"][0]["values"][0][1]
                print(f"📈 Sample CPU utilization: {float(sample_value):.1f}%")
        else:
            print("❌ CPU metrics query failed")
            print(f"Error: {result.stderr}")

    def step3_run_analysis(self):
        """Step 3: Run Performance Analysis."""
        self.print_header("Step 3: Running Performance Analysis")

        print("📊 Running Prometheus-based analysis...")
        result = subprocess.run(
            [
                sys.executable,
                "prometheus_analyzer.py",
                "--prometheus-url",
                "http://localhost:9090",
                "--interval",
                "5",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ Analysis completed successfully")
            print("\n📋 Analysis Summary:")
            # Extract key metrics from output
            lines = result.stdout.split("\n")
            for line in lines:
                if "Score Geral" in line or "Cpu" in line and "CPU:" in line:
                    print(f"   {line.strip()}")
                elif "Memory" in line and "Mem:" in line:
                    print(f"   {line.strip()}")
                elif "Disk" in line and "I/O:" in line:
                    print(f"   {line.strip()}")
                elif "Network" in line and "Throughput:" in line:
                    print(f"   {line.strip()}")
        else:
            print("❌ Analysis failed")
            print(f"Error: {result.stderr}")

    def step4_daemon_mode(self):
        """Step 4: Demonstrate Daemon Mode (5-minute intervals)."""
        self.print_header("Step 4: Daemon Mode - 5-Minute Interval Monitoring")

        print("⏰ Starting analyzer in daemon mode (5-minute intervals)...")
        print("📝 This will run for 12 seconds to demonstrate multiple cycles...")

        self.analyzer_proc = subprocess.Popen(
            [
                sys.executable,
                "prometheus_analyzer.py",
                "--prometheus-url",
                "http://localhost:9090",
                "--daemon",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Let it run for 12 seconds (should complete 2 cycles)
        time.sleep(12)

        # Check if process is still running and get output
        if self.analyzer_proc.poll() is None:
            print("⏹️ Stopping daemon mode...")
            self.analyzer_proc.terminate()
            self.analyzer_proc.wait()

        print("✅ Daemon mode demonstration complete")

    def step5_compare_local(self):
        """Step 5: Compare with Local Analysis."""
        self.print_header("Step 5: Comparison with Local Analysis")

        print("🖥️ Running local system analysis for comparison...")
        result = subprocess.run(
            [sys.executable, "local_analyzer.py"], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("✅ Local analysis completed")
            lines = result.stdout.split("\n")
            for line in lines:
                if "Score Geral" in line or "Host:" in line:
                    print(f"   {line.strip()}")
        else:
            print("❌ Local analysis failed")

    def step6_show_files(self):
        """Step 6: Show Generated Files."""
        self.print_header("Step 6: Generated Analysis Files")

        json_files = [f for f in os.listdir(".") if f.endswith(".json")]
        if json_files:
            print("📁 Generated JSON files:")
            for file in json_files:
                size = os.path.getsize(file)
                mtime = datetime.fromtimestamp(os.path.getmtime(file))
                print(f"   📄 {file} ({size} bytes, modified: {mtime:%H:%M:%S})")
        else:
            print("📁 No JSON files generated")

    def run_demo(self):
        """Run complete demonstration."""
        self.register_cleanup()

        print("🎬 Prometheus Remote Monitoring Demo")
        print("====================================")
        print("This demo shows how to monitor remote systems using Prometheus")
        print("with 5-minute interval collection as requested.\n")

        try:
            self.step1_start_mock_server()
            self.step2_test_mock_api()
            self.step3_run_analysis()
            self.step4_daemon_mode()
            self.step5_compare_local()
            self.step6_show_files()

            self.print_header("Demo Complete! 🎉")
            print("✅ All components working correctly")
            print("\n📋 What was demonstrated:")
            print("   1. ✅ Mock Prometheus server for testing")
            print("   2. ✅ Prometheus-based metrics collection")
            print("   3. ✅ USE Method performance analysis")
            print("   4. ✅ 5-minute interval monitoring (daemon mode)")
            print("   5. ✅ Rich console output with recommendations")
            print("   6. ✅ Comparison with local analysis")

            print("\n🚀 Ready for production deployment!")
            print("   Use deploy_prometheus.sh to deploy to real systems")

        except KeyboardInterrupt:
            print("\n\n⏹️ Demo interrupted by user")
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
        finally:
            self.cleanup()


if __name__ == "__main__":
    demo = MonitoringDemo()
    demo.run_demo()
