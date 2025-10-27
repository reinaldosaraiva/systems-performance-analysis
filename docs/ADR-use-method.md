# ADR-001: USE Method Implementation

## Status
Accepted

## Context
Precisamos implementar uma metodologia sistemática para análise de performance de sistemas Linux/Unix. A ferramenta deve identificar bottlenecks de forma consistente e fornecer scores quantitativos para tomada de decisão.

## Decision
Adotar o **USE Method** (Utilization, Saturation, Errors) de Brendan Gregg como metodologia principal de análise.

### Por que USE Method?
1. **Sistemático**: Cobertura completa de todas as métricas importantes
2. **Quantitativo**: Scores 0-100% para comparação objetiva
3. **Universal**: Aplicável a todos os tipos de sistemas
4. **Proven**: Metodologia validada em produção por 15+ anos
5. **Simple**: Fácil de entender e implementar

## Consequences

### Positivas
- Análise consistente across diferentes sistemas
- Identificação rápida de bottlenecks principais
- Métricas comparáveis ao longo do tempo
- Alinhamento com best practices de performance engineering

### Negativas
- Requer coleta de métricas adicionais (saturation)
- Thresholds fixos podem não se aplicar a todos os workloads
- Maior complexidade na coleta de dados

## Implementation Details

### Métricas por Componente

#### CPU
- **Utilization**: % CPU time used (psutil.cpu_percent)
- **Saturation**: Load average / CPU count
- **Errors**: CPU throttling events, scheduler errors

#### Memory
- **Utilization**: % memory used (psutil.virtual_memory)
- **Saturation**: Swap usage + OOM events
- **Errors**: Memory allocation failures

#### Disk
- **Utilization**: % time device busy (psutil.disk_io_counters)
- **Saturation**: I/O queue depth
- **Errors**: I/O error count

#### Network
- **Utilization**: % bandwidth used
- **Saturation**: Packet drops, retransmits
- **Errors**: Interface errors, connection failures

### Score Calculation

```python
def calculate_use_score(utilization: float, saturation: float, errors: float) -> Dict:
    """Calcula USE scores 0-100% com thresholds padrão."""
    return {
        "utilization_score": min(utilization, 100),
        "saturation_score": min(saturation, 100),
        "errors_score": min(errors * 100, 100),
        "overall_score": max(utilization, saturation, errors * 100),
        "status": _determine_status(utilization, saturation, errors)
    }

def _determine_status(u: float, s: float, e: float) -> str:
    """Determina status baseado nos thresholds."""
    if e > 0:
        return "CRITICAL"
    elif u > 80 or s > 20:
        return "WARNING"
    else:
        return "OK"
```

### Thresholds

| Component | Utilization | Saturation | Errors |
|-----------|-------------|-------------|--------|
| CPU | > 80% | > 20% | > 0 |
| Memory | > 85% | > 10% | > 0 |
| Disk | > 70% | > 30% | > 0 |
| Network | > 80% | > 15% | > 0 |

## Alternatives Considered

### RED Method (Rate, Errors, Duration)
- **Pros**: Focado em serviços, bom para SRE
- **Cons**: Menos abrangente para system performance
- **Rejected**: Não cobre utilization de recursos

### Four Golden Signals (Latency, Traffic, Errors, Saturation)
- **Pros**: Padrão Google SRE
- **Cons**: Focado em serviços, não em system resources
- **Rejected**: Não cobre todos os aspectos de system performance

### Custom Metrics
- **Pros**: Flexível para workload específico
- **Cons**: Não comparável, complexidade alta
- **Rejected**: Dificulta padronização e comparação

## Validation

### Test Cases
1. **CPU Bound System**: U>90%, S>50%, E=0 → WARNING
2. **Memory Pressure**: U>85%, S>30%, E>0 → CRITICAL
3. **Healthy System**: U<50%, S<10%, E=0 → OK
4. **Disk I/O Issues**: U<30%, S>80%, E>0 → CRITICAL

### Success Metrics
- Identificação correta de bottlenecks em 95% dos casos
- Scores correlacionam com performance percebida
- Análise completa em < 5 segundos
- Falsos positivos < 5%

## Future Considerations

### Adaptive Thresholds
- Workload-specific thresholds
- Machine learning para otimização
- Historical baseline comparison

### Extended Metrics
- Application-level metrics
- Container-specific metrics
- Cloud provider metrics

### Integration
- Prometheus/Grafana integration
- Alerting baseado em USE scores
- Automated remediation suggestions

---

**Date**: 2025-01-22
**Author**: Reinaldo Saraiva
**Status**: Implemented
**Review Date**: 2025-04-22