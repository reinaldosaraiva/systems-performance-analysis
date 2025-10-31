# 🚀 System Performance Analysis - USE Method Dashboard

A comprehensive system performance analysis tool based on **Brendan Gregg's USE Method** with **AI-powered insights** and **real-time monitoring**.

## ✨ Features

- 🎯 **Unified USE Method Dashboard** - Single pane of glass for performance analysis
- 🤖 **Dual AI Analysis** - LLM (Ollama MiniMax-M2) + AutoGen Multi-Agent insights
- 📊 **Real-time Metrics** - Prometheus + Grafana integration
- 🔍 **60-Second Checklist** - Quick system diagnosis following Brendan Gregg's methodology
- 📈 **Smart Recommendations** - Actionable technical recommendations with confidence scores
- 🏗️ **DDD Architecture** - Domain-Driven Design with clean architecture principles

## 🚦 Quick Start

### 1. Start the Monitoring Stack

```bash
# Start Prometheus, Grafana, and Node Exporter
docker-compose up -d

# Verify services
docker ps
```

### 2. Start the Brendan API Server

```bash
# Install dependencies
uv sync

# Start the API (provides AI insights)
uv run python src/brendan_api_server.py --host 0.0.0.0 --port 8080
```

### 3. Access the Dashboard

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

## 📖 Documentation

- **USE Method**: https://www.brendangregg.com/usemethod.html
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
