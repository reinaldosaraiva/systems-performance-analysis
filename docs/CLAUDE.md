# CLAUDE.md - Rules & Memories for Systems Performance Analysis

## 🎯 Global Rules

### Métricas e Units
- **SEMPRE** inclua unidades em todas as métricas (%, MB/s, ms, etc.)
- Formato: `valor (unidade)` - ex: `85.2 (%)`, `1.2 (GB/s)`
- Use precisão de 1 casa decimal para percentuais
- Use precisão de 2 casas para tempos (ms, μs)

### USE Method Implementation
- **SEMPRE** aplicar USE Method: Utilization, Saturation, Errors
- Scores: 0-100% para cada métrica
- Thresholds fixos: U>80% WARNING, S>20% WARNING, E>0% CRITICAL
- Documentar fórmulas de cálculo em comentários

### Code Patterns
- Classes com Single Responsibility Principle
- Métodos com type hints e docstrings
- Error handling com try/except específicos
- Logging estruturado com níveis apropriados

### Performance Considerations
- psutil calls com interval=1 para CPU
- Cache de métricas para análises repetidas
- Non-blocking I/O para coleta de dados
- Memory profiling para detectar leaks

## 🧠 Memory Patterns

### System Metrics Collection
```python
# Pattern para coleta de métricas
def collect_component_metrics(self, component: str) -> Dict[str, Any]:
    """Coleta métricas com tratamento de erro e unidades."""
    try:
        if component == "cpu":
            metrics = psutil.cpu_percent(interval=1)
            return {"utilization": metrics, "unit": "%"}
    except Exception as e:
        logger.error(f"Failed to collect {component}: {e}")
        return {"error": str(e), "unit": "error"}
```

### USE Analysis Pattern
```python
# Pattern para análise USE
def analyze_use_scores(self, metrics: Dict) -> Dict[str, Dict]:
    """Aplica USE Method com scores 0-100%."""
    result = {}
    for component, data in metrics.items():
        utilization = data.get("utilization", 0)
        saturation = data.get("saturation", 0)
        errors = data.get("errors", 0)
        
        result[component] = {
            "utilization_score": min(utilization, 100),
            "saturation_score": min(saturation, 100),
            "errors_score": min(errors * 100, 100),
            "status": self._calculate_status(utilization, saturation, errors)
        }
    return result
```

### Report Generation Pattern
```python
# Pattern para geração de relatórios
def generate_report(self, analysis: Dict, format: str = "html") -> str:
    """Gera relatório com gráficos e recomendações."""
    if format == "html":
        return self._generate_html_report(analysis)
    elif format == "markdown":
        return self._generate_markdown_report(analysis)
    else:
        raise ValueError(f"Unsupported format: {format}")
```

## 📋 Context Engineering Guidelines

### Document Structure
- `docs/` para contexto de longo prazo
- `docs/libs/` para documentação de bibliotecas via MCP
- Manter README.md atualizado com comandos
- ADRs para decisões arquiteturais importantes

### MCP Integration
- Usar Context7 para documentação de bibliotecas
- Gerar MDs em `docs/libs/` automaticamente
- Consultar docs/libs antes de usar APIs novas
- Manter script `setup-mcp.py` atualizado

### Token Optimization
- Chats por subtarefa para evitar sliding window
- Consultas seletivas a docs/libs
- Usar modelos com janelas amplas (GPT-4o-mini)
- Priorizar contexto para tarefas complexas

## 🚨 Anti-Patterns to Avoid

### ❌ Métricas sem Unidades
```python
# ERRADO
cpu_usage = psutil.cpu_percent()

# CORRETO
cpu_usage = psutil.cpu_percent(interval=1)  # (%)
```

### ❌ USE Method Incompleto
```python
# ERRADO - só verifica utilization
if cpu_usage > 80:
    status = "WARNING"

# CORRETO - USE Method completo
status = self._calculate_use_status(
    utilization=cpu_usage,
    saturation=load_avg,
    errors=error_rate
)
```

### ❌ Error Handling Genérico
```python
# ERRADO
try:
    metrics = collect_metrics()
except:
    pass

# CORRETO
try:
    metrics = collect_metrics()
except psutil.AccessDenied:
    logger.warning("Need elevated privileges for some metrics")
    metrics = self._collect_safe_metrics()
except Exception as e:
    logger.error(f"Metrics collection failed: {e}")
    raise
```

## 🎨 Persona Integration

### Reinaldo Saraiva Profile
- **Role**: Arquiteto Sênior de Infra em Nuvem (15 anos)
- **Focus**: Eficiência, segurança, redução de custos
- **Skills**: Python/FastAPI, Ansible/Terraform, AWS/Azure
- **Style**: Prático, com métricas e recomendações acionáveis

### Report Tone
- Linguagem técnica mas acessível
- Sempre incluir recomendações práticas
- Referenciar projetos reais quando possível
- Incluir lições aprendidas e best practices

### Example Recommendations
```python
def _generate_recommendations(self, analysis: Dict) -> List[str]:
    """Gera recomendações baseadas na análise USE."""
    recommendations = []
    
    if analysis["cpu"]["utilization_score"] > 80:
        recommendations.append(
            "🔥 CPU alta (>80%): Considere scale-up horizontal ou "
            "otimização de algoritmos. Em projetos de cloud, "
            "review de auto-scaling policies recomendado."
        )
    
    return recommendations
```

## 🔄 Development Workflow

### PRP Integration
- Estruturar tasks como PRPs
- Incluir All Needed Context com URLs/files
- Validar com pytest em 3 níveis
- Manter Confidence Score > 8.0

### Testing Strategy
- Unit tests para cada componente
- Integration tests para workflow completo
- Mock psutil calls para testes determinísticos
- Coverage > 80% obrigatório

### Documentation Updates
- Atualizar README.md para novas features
- Manter ADRs para decisões técnicas
- Gerar diagramas Mermaid para workflows
- Sincronizar docs/libs/ com novas dependências

## 📊 Quality Gates

### Code Quality
- PEP 8 compliance (flake8/ruff)
- Type hints para todas as funções
- Docstrings following Google style
- Complexidade ciclomática < 10

### Performance Requirements
- Coleta de métricas < 5 segundos
- Geração de relatórios < 30 segundos
- Memory usage < 100MB para análise completa
- CPU usage < 10% durante coleta

### Security Considerations
- Sem senhas hard-coded
- Privilégios mínimos necessários
- Sanitização de inputs
- Logging sem dados sensíveis

---

**Last Updated**: 2025-01-22
**Maintainer**: Reinaldo Saraiva
**Version**: 1.0.0