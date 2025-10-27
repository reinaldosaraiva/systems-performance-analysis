# Systems Performance Analysis Tool

Ferramenta de análise de performance de sistemas Linux/Unix baseada nas metodologias de Brendan Gregg (USE Method, Latency Analysis) com context engineering para IA.

## 🚀 Quick Start

### Pré-requisitos
- Python 3.10+
- uv (gestor de dependências moderno)
- Linux/Unix system

### Instalação
```bash
# Clonar o projeto
git clone <repo-url>
cd systems-performance

# Instalar dependências com uv
uv sync

# Ativar ambiente virtual
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows
```

### Execução
```bash
# Análise única
uv run python src/main.py --output report.html

# Análise com scheduler diário
uv run python src/main.py --schedule --time "08:00"

# Análise de componentes específicos
uv run python src/main.py --components cpu,memory --format markdown
```

## 📋 Context Engineering

### Documentos de Contexto
- `CLAUDE.md` - Rules e memories para IA
- `ADR-use-method.md` - Decisão arquitetural: USE Method
- `plano-acao.yaml` - Visão alta-nível do projeto
- `tarefa-todo.md` - TODO detalhado
- `state.local.md` - Estado atual do projeto
- `workflow.md` - Diagramas Mermaid do fluxo

### Bibliotecas Documentation
Documentação das bibliotecas gerada via MCP Context7:
- `docs/libs/PSUTIL.md` - psutil system metrics
- `docs/libs/MATPLOTLIB.md` - matplotlib visualization
- `docs/libs/UV.md` - uv dependency manager

## 🧪 Testes

```bash
# Executar todos os testes
uv run pytest -v

# Coverage
uv run pytest --cov=src --cov-report=html

# Testes específicos
uv run pytest tests/test_analysis.py -v
```

## 📊 Relatórios

Os relatórios são gerados em:
- `reports/` - Relatórios HTML e Markdown
- `reports/templates/` - Templates HTML personalizados

Formatos suportados:
- HTML (com gráficos matplotlib)
- Markdown
- JSON (para integração)

## ⚙️ Configuração

Variáveis de ambiente:
```bash
export SYSTEM_PERFORMANCE_LOG_LEVEL=INFO
export SYSTEM_PERFORMANCE_OUTPUT_DIR=./reports
export SYSTEM_PERFORMANCE_SCHEDULE_TIME=08:00
```

## 🔧 MCP Setup

Para gerar documentação das bibliotecas:
```bash
uv run python scripts/setup-mcp.py
```

## 📈 Métricas Coletadas

### CPU
- Utilization (%)
- Load averages (1m, 5m, 15m)
- Context switches
- CPU time by mode

### Memory
- Total/Available/Used
- Swap usage
- Buffer/Cache
- Memory pressure

### Disk
- I/O operations
- Throughput (MB/s)
- Utilization (%)
- Queue depth

### Network
- Interface throughput
- Packet drops/errors
- Connection states
- Latency percentiles

## 🎯 USE Method Scores

Cada componente recebe scores 0-100%:
- **Utilization**: % de tempo em uso
- **Saturation**: % de tempo sobrecarregado
- **Errors**: Taxa de erros

Thresholds:
- U > 80%: WARNING
- S > 20%: WARNING
- E > 0%: CRITICAL

## 📝 Desenvolvimento

### Estrutura do Projeto
```
systems-performance/
├── src/                    # Código principal
├── docs/                   # Context engineering
├── tests/                  # Testes pytest
├── scripts/                # Scripts utilitários
├── reports/                # Relatórios gerados
└── pyproject.toml          # Configuração uv
```

### Contribuição
1. Seguir PEP 8
2. Adicionar tests para novas features
3. Atualizar documentação em docs/
4. Usar context engineering patterns

## 🤖 Para IA (Claude/Gemini)

### Context Engineering Rules
- Sempre consultar `docs/CLAUDE.md` antes de modificar código
- Usar `docs/libs/` para referência de bibliotecas
- Manter janelas de contexto otimizadas
- Seguir PRP workflow para novas features

### Comandos Úteis
```bash
# Análise completa com contexto
/full-context "implementar nova análise de disk I/O"

# Code review com regras
/code-review src/collectors.py

# Atualizar docs
/update-docs collectors
```

## 📞 Suporte

Reinaldo Saraiva - Arquiteto Sênior de Infra em Nuvem
- Email: reinaldo.saraiva@example.com
- LinkedIn: linkedin.com/in/reinaldosaraiva

---

#Performance #SystemsEngineering #DevOps #ContextEngineering