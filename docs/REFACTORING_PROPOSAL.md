# 🏗️ Proposta de Refatoração - Estrutura DDD

## 📋 Análise da Estrutura Atual

### Problemas Identificados:

```
src/
├── __init__.py                    # 11 linhas
├── analyzers.py                   # 458 linhas ❌ Mistura domain + application
├── autogen_agents.py              # 1054 linhas ❌ Arquivo gigante
├── autogen_integration.py         # 1374 linhas ❌ MUITO GRANDE!
├── brendan_api_server.py          # 1007 linhas ❌ API + logic juntos
├── brendan_gregg_cli.py           # 564 linhas ❌ CLI + orchestration
├── brendan_gregg_persona.py       # 906 linhas ❌ Domain + infrastructure
├── brendan_llm_agent.py           # 789 linhas ❌ Domain + infra LLM
├── collectors.py                  # 416 linhas ❌ Infrastructure como domain
├── main.py                        # 491 linhas ❌ Orchestration + domain
├── remote_server.py               # 561 linhas ❌ API + infra
├── reporters.py                   # 811 linhas ❌ Application + rendering
└── time_series_db.py              # 429 linhas ❌ Infrastructure exposto
```

**Total: 8,871 linhas em 13 arquivos sem organização!**

---

## 🎯 Nova Estrutura Proposta (DDD + Hexagonal Architecture)

```
src/
├── __init__.py
│
├── domain/                                    # 🏛️ CORE: Business Logic
│   ├── __init__.py
│   │
│   ├── performance/                           # Bounded Context: Performance Analysis
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── system_metrics.py             # Entity: SystemMetrics
│   │   │   └── performance_insight.py        # Entity: PerformanceInsight
│   │   ├── value_objects/
│   │   │   ├── __init__.py
│   │   │   ├── severity.py                   # VO: Severity (CRITICAL, HIGH, etc)
│   │   │   ├── metric_value.py               # VO: MetricValue
│   │   │   └── threshold.py                  # VO: Threshold
│   │   ├── aggregates/
│   │   │   ├── __init__.py
│   │   │   └── analysis_session.py           # Aggregate: AnalysisSession
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── use_method_analyzer.py        # Domain Service: USE Method
│   │   │   └── bottleneck_detector.py        # Domain Service
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── metrics_repository.py         # Interface (port)
│   │   └── events/
│   │       ├── __init__.py
│   │       ├── insight_generated.py          # Event: InsightGenerated
│   │       └── analysis_completed.py         # Event: AnalysisCompleted
│   │
│   └── ai_agent/                              # Bounded Context: AI Agent
│       ├── __init__.py
│       ├── entities/
│       │   ├── __init__.py
│       │   ├── brendan_persona.py            # Entity: BrendanPersona
│       │   └── ai_insight.py                 # Entity: AIInsight
│       ├── value_objects/
│       │   ├── __init__.py
│       │   ├── llm_config.py                 # VO: LLMConfig
│       │   └── analysis_prompt.py            # VO: AnalysisPrompt
│       ├── services/
│       │   ├── __init__.py
│       │   ├── llm_analyzer.py               # Domain Service: LLM Analysis
│       │   └── prompt_builder.py             # Domain Service
│       └── repositories/
│           ├── __init__.py
│           └── llm_repository.py             # Interface (port)
│
├── application/                               # 🎯 USE CASES: Application Logic
│   ├── __init__.py
│   │
│   ├── use_cases/
│   │   ├── __init__.py
│   │   │
│   │   ├── performance/
│   │   │   ├── __init__.py
│   │   │   ├── analyze_system.py             # UC: Analyze System Performance
│   │   │   ├── generate_report.py            # UC: Generate Report
│   │   │   └── detect_bottlenecks.py         # UC: Detect Bottlenecks
│   │   │
│   │   └── ai_agent/
│   │       ├── __init__.py
│   │       ├── generate_llm_insights.py      # UC: Generate LLM Insights
│   │       └── run_autogen_analysis.py       # UC: Run AutoGen Multi-Agent
│   │
│   ├── dto/                                   # Data Transfer Objects
│   │   ├── __init__.py
│   │   ├── analysis_request.py
│   │   ├── analysis_response.py
│   │   └── insight_dto.py
│   │
│   ├── services/                              # Application Services (orchestration)
│   │   ├── __init__.py
│   │   ├── analysis_orchestrator.py          # Orchestrates analysis workflow
│   │   └── report_generator.py               # Generates reports (calls domain)
│   │
│   └── ports/                                 # Interfaces (Hexagonal Ports)
│       ├── __init__.py
│       ├── input/                             # Primary Ports (driven)
│       │   ├── __init__.py
│       │   ├── analysis_service.py           # Interface for API/CLI
│       │   └── report_service.py
│       └── output/                            # Secondary Ports (drivers)
│           ├── __init__.py
│           ├── metrics_collector.py          # Interface for collectors
│           ├── llm_client.py                 # Interface for LLM
│           └── notification_service.py
│
├── infrastructure/                            # 🔧 ADAPTERS: External Systems
│   ├── __init__.py
│   │
│   ├── monitoring/                            # Adapter: Monitoring
│   │   ├── __init__.py
│   │   ├── prometheus_collector.py           # Implements metrics_collector
│   │   ├── psutil_collector.py               # Implements metrics_collector
│   │   └── grafana_client.py
│   │
│   ├── ai/                                    # Adapter: AI/LLM
│   │   ├── __init__.py
│   │   ├── ollama_client.py                  # Implements llm_client
│   │   ├── autogen_orchestrator.py           # AutoGen multi-agent
│   │   └── openai_client.py                  # OpenAI compatibility
│   │
│   ├── persistence/                           # Adapter: Persistence
│   │   ├── __init__.py
│   │   ├── victoria_metrics_repository.py    # Time-series DB
│   │   ├── file_repository.py                # File-based storage
│   │   └── redis_cache.py                    # Cache layer
│   │
│   ├── reporting/                             # Adapter: Reporting
│   │   ├── __init__.py
│   │   ├── html_reporter.py                  # HTML reports
│   │   ├── markdown_reporter.py              # Markdown reports
│   │   └── grafana_dashboard_updater.py      # Update dashboards
│   │
│   └── config/                                # Configuration
│       ├── __init__.py
│       ├── settings.py                       # App settings
│       └── container.py                      # Dependency Injection
│
├── presentation/                              # 🌐 INTERFACES: Entry Points
│   ├── __init__.py
│   │
│   ├── api/                                   # REST API (FastAPI)
│   │   ├── __init__.py
│   │   ├── main.py                           # FastAPI app
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── insights.py                   # /api/insights
│   │   │   ├── llm.py                        # /api/insights/llm
│   │   │   ├── health.py                     # /health
│   │   │   └── dashboard.py                  # /dashboard
│   │   ├── schemas/                          # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── insight_schema.py
│   │   │   └── analysis_schema.py
│   │   └── dependencies.py                   # FastAPI dependencies
│   │
│   ├── cli/                                   # Command Line Interface
│   │   ├── __init__.py
│   │   ├── main.py                           # CLI entry point
│   │   └── commands/
│   │       ├── __init__.py
│   │       ├── analyze.py                    # analyze command
│   │       ├── report.py                     # report command
│   │       └── brendan.py                    # brendan-ai command
│   │
│   └── remote/                                # Remote analysis server
│       ├── __init__.py
│       └── server.py
│
├── shared/                                    # 🔄 SHARED: Cross-cutting concerns
│   ├── __init__.py
│   ├── exceptions.py                         # Custom exceptions
│   ├── logging.py                            # Logging setup
│   ├── constants.py                          # Global constants
│   └── utils.py                              # Utility functions
│
└── tests/                                     # 🧪 TESTS: Mirror structure
    ├── __init__.py
    ├── unit/
    │   ├── domain/
    │   ├── application/
    │   └── infrastructure/
    ├── integration/
    │   ├── api/
    │   └── cli/
    └── e2e/
        └── scenarios/
```

---

## 🎯 Benefícios da Nova Estrutura

### 1️⃣ **Separação Clara de Responsabilidades**

```
Domain       → Regras de negócio puras (USE Method, análise)
Application  → Casos de uso (orquestração)
Infrastructure → Adaptadores externos (Prometheus, Ollama, DB)
Presentation → Interfaces (API, CLI)
```

### 2️⃣ **Testabilidade**

```python
# ANTES: Difícil testar (tudo acoplado)
from brendan_gregg_persona import BrendanGreggPersona
persona = BrendanGreggPersona()  # Depende de Prometheus, Grafana...

# DEPOIS: Fácil testar (dependency injection)
from domain.performance.services.use_method_analyzer import USEMethodAnalyzer
analyzer = USEMethodAnalyzer()  # Puro, sem dependências externas
```

### 3️⃣ **Reutilização**

```python
# Domain services podem ser usados por:
- API REST (FastAPI)
- CLI (typer/click)
- Background jobs (Celery)
- Testes automatizados
```

### 4️⃣ **Manutenibilidade**

```
ANTES: 1 arquivo com 1374 linhas
DEPOIS: 10 arquivos com ~150 linhas cada (mais fácil de entender)
```

### 5️⃣ **Escalabilidade**

Cada bounded context (performance, ai_agent) pode evoluir independentemente.

---

## 📦 Bounded Contexts Identificados

### 1. **Performance Analysis** (Core Domain)
- **Entidades**: SystemMetrics, PerformanceInsight, AnalysisSession
- **Value Objects**: Severity, MetricValue, Threshold
- **Domain Services**: USEMethodAnalyzer, BottleneckDetector
- **Responsabilidade**: Análise de performance usando USE Method

### 2. **AI Agent** (Supporting Domain)
- **Entidades**: BrendanPersona, AIInsight
- **Value Objects**: LLMConfig, AnalysisPrompt
- **Domain Services**: LLMAnalyzer, PromptBuilder
- **Responsabilidade**: Geração de insights usando IA (LLM, AutoGen)

### 3. **Monitoring** (Supporting Domain)
- **Adapters**: PrometheusCollector, PsutilCollector, GrafanaClient
- **Responsabilidade**: Coleta de métricas de sistemas externos

### 4. **Reporting** (Supporting Domain)
- **Adapters**: HTMLReporter, MarkdownReporter, GrafanaDashboardUpdater
- **Responsabilidade**: Geração de relatórios em múltiplos formatos

---

## 🔄 Plano de Migração

### Fase 1: Preparação (Sem quebrar funcionalidade)
1. ✅ Criar nova estrutura de pastas
2. ✅ Mover domain logic primeiro (entities, value objects)
3. ✅ Manter imports antigos funcionando (compatibilidade reversa)

### Fase 2: Refatoração Incremental
1. Migrar `collectors.py` → `infrastructure/monitoring/`
2. Migrar `analyzers.py` → `domain/performance/services/`
3. Migrar `brendan_gregg_persona.py` → `domain/ai_agent/`
4. Migrar `brendan_llm_agent.py` → `domain/ai_agent/services/`
5. Migrar `autogen_*.py` → `infrastructure/ai/`
6. Migrar `reporters.py` → `infrastructure/reporting/`
7. Migrar `brendan_api_server.py` → `presentation/api/`
8. Migrar `brendan_gregg_cli.py` → `presentation/cli/`

### Fase 3: Limpeza
1. Remover arquivos antigos do `src/` raiz
2. Atualizar imports em todos os arquivos
3. Atualizar testes
4. Atualizar documentação

### Fase 4: Otimização
1. Implementar dependency injection container
2. Adicionar eventos de domínio
3. Implementar CQRS se necessário
4. Adicionar cache layer

---

## 🛠️ Exemplo Prático de Refatoração

### ANTES: `src/brendan_gregg_persona.py` (906 linhas)

```python
# Tudo misturado: domain + infrastructure + application
class BrendanGreggPersona:
    def __init__(self, prometheus_url, grafana_url):
        self.prometheus = PrometheusClient(prometheus_url)  # ❌ Acoplado
        self.grafana = GrafanaClient(grafana_url)            # ❌ Acoplado

    def analyze_use_method(self):
        # ❌ Domain logic + infrastructure calls juntos
        cpu_util = self.prometheus.query("node_cpu...")
        insights = self._analyze_cpu(cpu_util)
        return insights
```

### DEPOIS: Separado em camadas

```python
# domain/ai_agent/entities/brendan_persona.py (domain puro)
@dataclass
class BrendanPersona:
    """Entity: Brendan Gregg Persona (domain logic puro)"""
    name: str = "Brendan Gregg"
    expertise: List[str] = field(default_factory=lambda: ["USE Method", "BPF"])

    def format_insight(self, metrics: SystemMetrics) -> str:
        """Formata insight no estilo Brendan (domain logic)"""
        # Sem dependências externas!
        return f"USE Method Analysis: {metrics}"

# domain/performance/services/use_method_analyzer.py (domain service)
class USEMethodAnalyzer:
    """Domain Service: Implementa USE Method (regra de negócio)"""

    def analyze(self, metrics: SystemMetrics) -> List[PerformanceInsight]:
        """Análise pura, sem I/O"""
        insights = []

        # CPU Analysis
        if metrics.cpu_utilization > 80:
            insights.append(PerformanceInsight(
                severity=Severity.HIGH,
                component="cpu",
                title="High CPU Utilization"
            ))

        return insights

# application/use_cases/ai_agent/generate_llm_insights.py (use case)
class GenerateLLMInsights:
    """Use Case: Orquestra geração de insights com LLM"""

    def __init__(
        self,
        metrics_collector: MetricsCollectorPort,  # Interface (port)
        llm_client: LLMClientPort,                # Interface (port)
        analyzer: USEMethodAnalyzer               # Domain service
    ):
        self.metrics_collector = metrics_collector
        self.llm_client = llm_client
        self.analyzer = analyzer

    async def execute(self, request: AnalysisRequest) -> AnalysisResponse:
        """Orquestra análise (application logic)"""
        # 1. Coleta métricas (via port)
        metrics = await self.metrics_collector.collect()

        # 2. Análise domain (use method)
        insights = self.analyzer.analyze(metrics)

        # 3. Enriquece com LLM (via port)
        ai_insights = await self.llm_client.generate_insights(metrics)

        # 4. Retorna resultado
        return AnalysisResponse(
            insights=insights + ai_insights,
            timestamp=datetime.now()
        )

# infrastructure/monitoring/prometheus_collector.py (adapter)
class PrometheusCollector(MetricsCollectorPort):
    """Adapter: Implementa coleta via Prometheus"""

    def __init__(self, prometheus_url: str):
        self.client = PrometheusClient(prometheus_url)

    async def collect(self) -> SystemMetrics:
        """Implementa interface do port"""
        cpu = await self.client.query("node_cpu...")
        memory = await self.client.query("node_memory...")

        return SystemMetrics(
            cpu_utilization=cpu,
            memory_utilization=memory
        )

# presentation/api/routes/insights.py (API endpoint)
@router.post("/insights/llm")
async def generate_llm_insights(
    request: AnalysisRequestSchema,
    use_case: GenerateLLMInsights = Depends(get_llm_insights_use_case)
):
    """API endpoint: Chama use case"""
    result = await use_case.execute(request.to_dto())
    return AnalysisResponseSchema.from_dto(result)
```

---

## 📊 Comparação de Métricas

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| **Arquivos na raiz** | 13 | 0 | ✅ 100% |
| **Maior arquivo** | 1374 linhas | ~200 linhas | ✅ 85% |
| **Acoplamento** | Alto | Baixo | ✅ |
| **Testabilidade** | Difícil | Fácil | ✅ |
| **Reutilização** | Limitada | Alta | ✅ |
| **Manutenibilidade** | Complexa | Simples | ✅ |

---

## 🎯 Próximos Passos

1. **Aprovar proposta** 👍
2. **Criar estrutura de pastas** (script automatizado)
3. **Migração incremental** (fase por fase)
4. **Testes garantindo funcionalidade**
5. **Atualização de documentação**

---

## 📚 Referências

- [Architecture Patterns with Python (Cosmic Python)](https://www.cosmicpython.com/)
- [Domain-Driven Design in Python](https://dddinpython.com/)
- [AWS: Hexagonal Architecture with Python](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/structure-a-python-project-in-hexagonal-architecture-using-aws-lambda.html)
- [Python Monorepo Best Practices](https://www.tweag.io/blog/2023-04-04-python-monorepo-1/)

---

**Autor:** Claude Code
**Data:** 29/10/2025
**Versão:** 1.0
