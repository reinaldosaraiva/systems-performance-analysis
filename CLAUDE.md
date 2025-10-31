# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Development Commands

### Environment Setup
```bash
# Install dependencies using uv (modern Python package manager)
uv sync

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
```

### Running the Application
```bash
# Full analysis with HTML report
uv run python src/main.py

# Analyze specific components
uv run python src/main.py --components cpu,memory

# Include latency analysis with markdown output
uv run python src/main.py --latency --format markdown

# Schedule daily analysis
uv run python src/main.py --schedule --time 08:00

# Start monitoring stack
docker-compose up -d

# Deploy Prometheus
./deploy_prometheus.sh

# Run AutoGen multi-agent analysis
uv run python src/autogen_integration.py
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test category
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m slow

# Run single test
uv run pytest -k "test_name" -v
```

### Code Quality
```bash
# Lint with ruff
uv run ruff check src/ tests/

# Type checking
uv run mypy src/ tests/

# Format code
uv run black src/ tests/
```

## Architecture Overview

### Core Components

1. **SystemCollector** (`src/collectors.py`)
   - Wraps psutil for system metrics collection
   - Handles CPU, memory, disk, and network metrics
   - Implements caching and Linux-specific features
   - Always use `interval=1` for CPU metrics

2. **USEAnalyzer** (`src/analyzers.py`)
   - Implements Brendan Gregg's USE Method
   - Calculates Utilization, Saturation, and Errors scores (0-100%)
   - Fixed thresholds: CPU U>80%, Memory U>85%, Disk U>70%, Network U>80%
   - Returns status classification and recommendations

3. **LatencyAnalyzer** (`src/analyzers.py`)
   - Analyzes latency distributions and percentiles
   - Calculates p50, p95, p99 metrics
   - Classifies performance (Excellent/Good/Fair/Poor)
   - Detects outliers and anomalies

4. **ReportGenerator** (`src/reporters.py`)
   - Generates HTML reports with matplotlib visualizations
   - Creates Markdown reports for CI/CD integration
   - Uses Jinja2 templating for HTML output
   - Includes executive summaries

5. **AutoGen Integration** (`src/autogen_integration.py`)
   - Multi-agent AI system with 6 specialized agents
   - Performance Analyst, Infrastructure Expert, Security Analyst
   - Cost Optimizer, Report Generator, Coordinator
   - Provides collaborative analysis and consensus recommendations

### Key Design Patterns

- **Single Responsibility**: Each class handles one specific concern
- **Type Hints**: All functions use type annotations
- **Error Handling**: Specific exception handling, not generic catches
- **Metrics Units**: Always include units (%, MB/s, ms) in format `value (unit)`
- **Logging**: Structured logging with appropriate levels

### Performance Considerations

- Analysis time must be < 5 seconds
- Memory usage < 100MB for complete analysis
- Use psutil caching to prevent excessive system calls
- Non-blocking I/O for metrics collection
- Docker containers for monitoring stack

### USE Method Implementation

The project strictly follows the USE Method with these thresholds:

| Component | Utilization | Saturation | Errors |
|-----------|-------------|------------|--------|
| CPU       | >80% WARNING | >20% WARNING | >0 CRITICAL |
| Memory    | >85% WARNING | >10% WARNING | >0 CRITICAL |
| Disk      | >70% WARNING | >30% WARNING | >0 CRITICAL |
| Network   | >80% WARNING | >15% WARNING | >0 CRITICAL |

### Monitoring Stack

Docker Compose includes:
- Prometheus (metrics collection and federation)
- Grafana (visualization on port 3000)
- VictoriaMetrics (90-day retention)
- AlertManager (alert routing)
- Node Exporter (host metrics)
- Redis (caching)
- Nginx (reverse proxy)

Remote federation endpoint: `http://177.93.132.48:9090`

### Testing Strategy

- Unit tests for individual components
- Integration tests for complete workflows
- Mock psutil calls for deterministic testing
- Target: >85% code coverage
- Use pytest markers: `unit`, `integration`, `slow`