# Process Health - Explicação do Valor 3.58e-13

## O que significa 3.58e-13?

O valor `3.58e-13` é notação científica para:
- **3.58 × 10⁻¹³**
- **0.000000000000358**
- **0.0000000000358%**

## Qual métrica está mostrando isso?

Este valor vem da métrica **File Descriptors Used %**, que calcula:
```
(node_filefd_allocated / node_filefd_maximum) * 100
```

## Isso é bom ou ruim?

**✅ EXCELENTE** - Este valor é extremamente positivo:

- **Uso mínimo**: O sistema está usando apenas 0.0000000000358% dos file descriptors disponíveis
- **Muita margem**: Há espaço abundante para mais processos abrirem arquivos
- **Sem risco**: Zero chance de esgotar recursos de file descriptors
- **Performance ideal**: Sem limitações por falta de file descriptors

## Outras métricas de Process Health:

- **Zombie Processes**: 0 (nenhum processo zumbi)
- **I/O Blocked Processes**: 0 (nenhum processo bloqueado por I/O)
- **File Descriptors**: 0.0000000000358% (uso mínimo)

## Conclusão

O sistema está em **estado perfeito** no que diz respeito à saúde de processos. O valor `3.58e-13` indica uma utilização extremamente baixa de file descriptors, o que é ideal para a saúde e performance do sistema.

## Ajuste Realizado

- **Unidade**: Alterada para "percent" com 2 casas decimais
- **Thresholds**: Ajustados para 50% (amarelo) e 80% (vermelho)
- **Legenda**: Simplificada para "File Descriptors %"

Agora o valor aparecerá como "0.00%" no dashboard, tornando-se mais fácil de entender.