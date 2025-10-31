# 🚀 System Performance Analysis - USE Method Dashboard

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)](https://github.com)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Ollama](https://img.shields.io/badge/ollama-required-orange)](https://ollama.com/)

> ✅ **FULLY IMPLEMENTED** - Production-ready with complete AI insights integration

A comprehensive system performance analysis tool based on **Brendan Gregg's USE Method** with **AI-powered insights** and **real-time monitoring**.

## ✨ Features

- 🎯 **Unified USE Method Dashboard** - Single pane of glass for performance analysis
- 🤖 **Dual AI Analysis** - LLM (Ollama MiniMax-M2) + AutoGen Multi-Agent insights
- 📊 **Real-time Metrics** - Prometheus + Grafana integration
- 🔍 **60-Second Checklist** - Quick system diagnosis following Brendan Gregg's methodology
- 📈 **Smart Recommendations** - Actionable technical recommendations with confidence scores
- 🏗️ **DDD Architecture** - Domain-Driven Design with clean architecture principles

## 📋 Prerequisites

Before starting, ensure you have the following installed:

### Required

1. **Python 3.11+**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **UV (Python Package Manager)**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Docker & Docker Compose**
   ```bash
   docker --version
   docker compose version
   ```

4. **Ollama with MiniMax-M2 Model** ⚠️ **REQUIRED**

   Install Ollama:
   ```bash
   # macOS
   brew install ollama

   # Linux
   curl -fsSL https://ollama.com/install.sh | sh

   # Or download from https://ollama.com/download
   ```

   Start Ollama service:
   ```bash
   # macOS/Linux - Start Ollama in background
   ollama serve
   ```

   Download MiniMax-M2 Cloud model:
   ```bash
   # This will download the model (~2-4GB)
   ollama pull minimax-m2:cloud

   # Verify installation
   ollama list | grep minimax
   ```

   **Why MiniMax-M2?**
   - 1 trillion parameters (DeepSeek-R1 class)
   - 71.6% on SWE-bench (5x cheaper than Claude)
   - Native reasoning capabilities
   - Optimized for technical analysis

### Optional

5. **Git** (for version control)
   ```bash
   git --version
   ```

## 🚦 Quick Start

### 1. Ensure Ollama is Running ⚠️

**IMPORTANT: Start Ollama BEFORE starting the API server**

```bash
# Start Ollama (keep this terminal open)
ollama serve

# In a new terminal, verify Ollama is ready
curl http://localhost:11434/api/tags

# Confirm minimax-m2:cloud model is available
ollama list | grep minimax-m2
```

### 2. Start the Monitoring Stack

```bash
# Start Prometheus, Grafana, and Node Exporter
docker-compose up -d

# Verify services
docker ps
```

### 3. Start the Brendan API Server

```bash
# Install dependencies
uv sync

# Start the API (provides AI insights)
uv run python src/brendan_api_server.py --host 0.0.0.0 --port 8080

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8080
# Connected to Ollama successfully
```

### 4. Access the Dashboard

```bash
# Open the Unified USE Method Dashboard
open "http://localhost:3000/d/d1e40598-6d0c-472c-950b-3e5c024f02e5"
```

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

## 📊 Dashboard Overview

The unified dashboard provides:

### 🤖 AI-Powered Insights (Top Panels)
- **LLM Insights** - Fast AI analysis using Ollama MiniMax-M2
- **AutoGen Multi-Agent** - Collaborative analysis from 5 specialized agents
- Full technical recommendations displayed inline

### 📋 60-Second Checklist
- **Uptime & Load** - CPU saturation indicators
- **System Events** - OOM kills, page faults, network errors
- **vmstat** - Running/blocked processes, swap activity

### 🔍 USE Method Analysis
- **CPU** - Utilization, Saturation (load), Errors (steal time)
- **Memory** - Utilization, Saturation (swap), ECC errors
- **Disk** - I/O time, queue depth, read/write errors
- **Network** - Throughput, drops, transmission errors

### 👁️ Dual Perspectives
- **Bottom-Up** - Resource-focused (Admin view)
- **Top-Down** - Workload-focused (Dev view)

### 🎯 Executive Summary
- Overall system health score
- Component-specific health metrics
- Clear pass/fail indicators

## 🤖 AI Analysis System

### LLM Insights (Ollama MiniMax-M2)
Fast, single-agent analysis with:
- Real-time performance bottleneck detection
- Confidence-scored recommendations (85%+)
- Root cause identification
- Immediate and long-term fixes

### AutoGen Multi-Agent
Collaborative analysis from 5 specialized agents:
1. **Performance Analyst** - USE Method expert (Brendan Gregg persona)
2. **Infrastructure Expert** - Cloud architecture & scaling
3. **Security Analyst** - OWASP & system hardening
4. **Cost Optimizer** - Cloud cost optimization
5. **Reliability Engineer** - SRE & incident response

## 📁 Project Structure

```
.
├── src/                          # Source code (DDD architecture)
│   ├── application/             # Use cases and business logic
│   ├── domain/                  # Core domain models
│   ├── infrastructure/          # External integrations
│   └── brendan_api_server.py   # FastAPI server
├── grafana/
│   └── dashboards/
│       └── unified-use-method-dashboard.json  # Main dashboard
├── docker/                      # Docker configurations
│   ├── docker-compose.yml      # Monitoring stack
│   └── prometheus_local.yml    # Prometheus config
├── scripts/                     # Utility scripts
│   ├── deploy_prometheus.sh    # Deploy Prometheus
│   └── start_monitoring.sh     # Start monitoring
└── tests/                       # Test suite

```

## 🛠️ Development

### Run Tests

```bash
uv run pytest
```

### Code Quality

```bash
# Lint
uv run ruff check src/

# Type checking
uv run mypy src/

# Format
uv run black src/
```

## 🔧 Troubleshooting

### Ollama Issues

**Problem: "Connection refused" or "Could not connect to Ollama"**

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start Ollama
ollama serve

# Keep it running in a separate terminal or use systemd/launchd
```

**Problem: "Model not found: minimax-m2:cloud"**

```bash
# Pull the model explicitly
ollama pull minimax-m2:cloud

# Verify it's downloaded
ollama list

# Expected output should include:
# minimax-m2:cloud    <size>    <date>
```

**Problem: Slow AI responses**

```bash
# Check Ollama logs
ollama logs

# Monitor system resources (Ollama uses CPU/GPU)
top -pid $(pgrep ollama)

# For Apple Silicon Macs, ensure Metal acceleration is working
# MiniMax-M2 should use Neural Engine when available
```

**Problem: API returns empty insights**

```bash
# Test Ollama directly
curl http://localhost:11434/api/generate -d '{
  "model": "minimax-m2:cloud",
  "prompt": "Say hello",
  "stream": false
}'

# Check Brendan API logs
# Look for Ollama connection errors in the API output
```

### Docker Issues

**Problem: Grafana dashboard not loading**

```bash
# Check if containers are running
docker ps

# Restart Grafana
docker restart system-performance-grafana-1

# Check Grafana logs
docker logs system-performance-grafana-1
```

**Problem: No metrics in Prometheus**

```bash
# Verify node-exporter is running
curl http://localhost:9100/metrics

# Check Prometheus targets
open http://localhost:9090/targets

# Restart Prometheus
docker restart system-performance-prometheus-1
```

### Port Conflicts

If ports are already in use:

```bash
# Check what's using the ports
lsof -i :3000  # Grafana
lsof -i :8080  # Brendan API
lsof -i :9090  # Prometheus
lsof -i :11434 # Ollama

# Kill processes if needed
kill -9 <PID>
```

## 📖 Documentation

- **USE Method**: https://www.brendangregg.com/usemethod.html
- **Ollama**: https://ollama.com/
- **MiniMax-M2 Model**: https://ollama.com/library/minimax-m2
- **CLAUDE.md**: Project-specific Claude Code instructions
- **NEXT_STEPS.md**: Development roadmap and future improvements

## 🔗 Key Endpoints

- **Grafana Dashboard**: http://localhost:3000/d/d1e40598-6d0c-472c-950b-3e5c024f02e5
- **Brendan API**: http://localhost:8080
- **LLM Insights API**: http://localhost:8080/api/insights/llm
- **AutoGen Insights API**: http://localhost:8080/api/insights/autogen
- **Prometheus**: http://localhost:9090

## 📝 License

MIT License - See LICENSE file for details
