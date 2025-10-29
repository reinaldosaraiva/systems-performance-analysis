# Grafana Integration - Brendan Gregg Agent Analysis

## Visão Geral

Este documento explica como integrar a análise do agente Brendan Gregg com dashboards do Grafana, permitindo visualizar insights de performance em tempo real.

## 🎯 O Que Foi Implementado

### 1. API REST para Insights
- **Arquivo**: `src/brendan_api_server.py`
- **Funcionalidade**: Servidor FastAPI que expõe insights do agente via REST API
- **Endpoints**: Health, insights, summary, por severidade, por componente
- **Compatibilidade**: SimpleJson data source do Grafana

### 2. Dashboard Grafana
- **Arquivo**: `grafana/dashboards/brendan-agent-analysis.json`
- **Funcionalidade**: Dashboard completo com visualizações de insights
- **Painéis**: Stats, gráficos de pizza, tabelas, logs detalhados

### 3. Integração na CLI
- **Flags**: `--serve`, `--api-host`, `--api-port`
- **Funcionalidade**: Inicia API server após análise
- **Uso**: Disponível em `main.py` e `brendan_gregg_cli.py`

## 🚀 Como Usar

### Passo 1: Executar Análise com API Server

```bash
# Executar análise e iniciar API server
uv run python src/main.py --brendan-analysis --serve

# Com configurações customizadas
uv run python src/main.py --brendan-analysis --serve \
    --api-host 0.0.0.0 \
    --api-port 8080 \
    --prometheus http://localhost:9090 \
    --grafana http://localhost:3000
```

### Passo 2: Configurar Data Source no Grafana

1. **Acessar Grafana**: http://localhost:3000
2. **Ir para**: Configuration → Data Sources → Add data source
3. **Selecionar**: JSON API (ou SimpleJson se instalado)
4. **Configurar**:
   - **Name**: Brendan Agent API
   - **URL**: http://localhost:8080
   - **Access**: Server (default)
5. **Salvar e Testar**

### Passo 3: Importar Dashboard

#### Método 1: Via Interface do Grafana

1. **Ir para**: Dashboards → Import
2. **Upload JSON**: Selecionar `grafana/dashboards/brendan-agent-analysis.json`
3. **Selecionar Data Source**: Brendan Agent API
4. **Importar**

#### Método 2: Via API do Grafana

```bash
# Com curl
curl -X POST \
  http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @grafana/dashboards/brendan-agent-analysis.json

# Com script Python
uv run python scripts/import_grafana_dashboard.py \
    --dashboard grafana/dashboards/brendan-agent-analysis.json \
    --grafana http://localhost:3000 \
    --user admin \
    --password admin
```

### Passo 4: Visualizar Insights

1. **Acessar Dashboard**: http://localhost:3000/d/brendan-agent-analysis
2. **Dashboard URL**: Brendan Gregg Agent - Performance Analysis
3. **Refresh**: O dashboard atualiza a cada 30 segundos

## 📊 Painéis do Dashboard

### Overview (Linha 1)

#### Total Insights
- **Tipo**: Stat
- **Descrição**: Número total de insights detectados
- **Threshold**: Verde < 3, Amarelo < 5, Vermelho >= 5

#### Critical Issues
- **Tipo**: Stat
- **Descrição**: Insights com severidade CRITICAL
- **Cor**: Fundo vermelho se > 0

#### High Severity
- **Tipo**: Stat
- **Descrição**: Insights com severidade HIGH
- **Cor**: Fundo laranja se > 0

#### API Health
- **Tipo**: Stat
- **Descrição**: Status da API (✓ HEALTHY)
- **Cor**: Verde quando saudável

### Distribuição (Linha 2)

#### Issues by Severity (Esquerda)
- **Tipo**: Donut Chart
- **Dados**: Distribuição por CRITICAL, HIGH, MEDIUM, LOW
- **Cores**: Vermelho, Laranja, Amarelo, Verde

#### Issues by Component (Direita)
- **Tipo**: Pie Chart
- **Dados**: Distribuição por CPU, Memory, Disk, Network
- **Cores**: Palette padrão

### Tabela Detalhada (Linha 3)

#### All Insights - Detailed View
- **Tipo**: Table
- **Colunas**: Time, Severity, Component, Issue, Details, Method
- **Recursos**:
  - Ordenação por qualquer coluna
  - Cores de fundo em Severity e Component
  - Mostra observações completas

### Logs Detalhados (Linha 4)

#### Critical Insights - Details (Esquerda)
- **Tipo**: Logs
- **Dados**: Apenas insights CRITICAL
- **Recursos**: Mostra timestamp, detalhes completos

#### High Severity Insights - Details (Direita)
- **Tipo**: Logs
- **Dados**: Apenas insights HIGH
- **Recursos**: Mostra timestamp, detalhes completos

### Latest Insight (Linha 5)

#### Último Insight Detectado
- **Tipo**: Text (Markdown)
- **Dados**: Insight mais recente com todos os detalhes
- **Inclui**:
  - Título
  - Componente e Severidade
  - Observação
  - Root Cause
  - Immediate Action

## 🔌 API Endpoints

### Health Check
```bash
GET /health
```
**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-28T15:55:33.753611"
}
```

### Summary
```bash
GET /api/insights/summary
```
**Response**:
```json
{
  "total_insights": 2,
  "by_severity": {
    "HIGH": 1,
    "MEDIUM": 1
  },
  "by_component": {
    "cpu": 1,
    "system": 1
  },
  "timestamp": "2025-10-28T15:56:29.663484"
}
```

### All Insights
```bash
GET /api/insights?limit=100
```
**Parameters**:
- `limit`: Máximo de insights a retornar (1-1000)
- `severity`: Filtrar por severidade (CRITICAL, HIGH, MEDIUM, LOW)
- `component`: Filtrar por componente (cpu, memory, disk, network)

**Response**:
```json
{
  "total": 2,
  "insights": [
    {
      "title": "CPU Saturation Detected",
      "severity": "HIGH",
      "component": "cpu",
      "evidence": {
        "load_average_1m": 20.17,
        "cpu_count": 8.0,
        "load_per_cpu": 2.52
      },
      "observation": "Load average per CPU is 2.52x",
      "root_cause": "High number of runnable processes",
      "immediate_action": "Check run queue with vmstat"
    }
  ],
  "timestamp": "2025-10-28T15:56:35.104491"
}
```

### By Severity
```bash
GET /api/insights/severity/{severity}
```
**Parameters**: `severity` = CRITICAL | HIGH | MEDIUM | LOW

### By Component
```bash
GET /api/insights/component/{component}
```
**Parameters**: `component` = cpu | memory | disk | network

### Latest Insight
```bash
GET /api/insights/latest
```

### Grafana SimpleJson Endpoints

#### Search (Metrics Discovery)
```bash
GET /search
POST /search
```
**Response**: Lista de métricas disponíveis

#### Query (Time Series Data)
```bash
POST /query
```
**Body**:
```json
[
  {
    "target": "all",
    "range": {
      "from": "2025-10-28T00:00:00Z",
      "to": "2025-10-28T23:59:59Z"
    }
  }
]
```

#### Annotations (Eventos no Gráfico)
```bash
GET /annotations
POST /annotations
```
**Response**: Lista de insights como anotações no Grafana

## 🛠️ Configuração Avançada

### Custom API Host e Port

```bash
# Bind apenas localhost
uv run python src/main.py --brendan-analysis --serve \
    --api-host 127.0.0.1 \
    --api-port 9999

# Bind todas interfaces (acessível remotamente)
uv run python src/main.py --brendan-analysis --serve \
    --api-host 0.0.0.0 \
    --api-port 8080
```

### Executar API Server Standalone

```bash
# Servidor standalone (sem executar análise)
uv run python src/brendan_api_server.py \
    --host 0.0.0.0 \
    --port 8080 \
    --reports-dir reports \
    --log-level INFO
```

**Uso**: Útil quando já tem relatórios gerados e quer apenas servir via API.

### CORS Configuration

A API já vem configurada com CORS habilitado para permitir acesso do Grafana:

```python
allow_origins=["*"]  # Permite todas as origens
allow_methods=["*"]  # Permite todos os métodos HTTP
allow_headers=["*"]  # Permite todos os headers
```

**Produção**: Restrinja `allow_origins` para apenas o domínio do Grafana.

### Reverse Proxy (Nginx)

Se quiser expor a API via Nginx:

```nginx
location /brendan-api/ {
    proxy_pass http://localhost:8080/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**Acesso**: http://yourserver/brendan-api/health

## 📈 Workflow Completo

### 1. Análise Contínua

```bash
#!/bin/bash
# Script: continuous_analysis.sh

while true; do
    echo "Running Brendan Gregg analysis..."
    uv run python src/main.py --brendan-analysis --verbose

    echo "Waiting 5 minutes..."
    sleep 300
done
```

### 2. Com API Server Persistente

```bash
#!/bin/bash
# Terminal 1: Executar API server persistente
uv run python src/brendan_api_server.py --port 8080

# Terminal 2: Executar análises periódicas
while true; do
    uv run python src/main.py --brendan-analysis --verbose
    sleep 300
done
```

### 3. Agendamento com Cron

```bash
# Adicionar ao crontab
# Executar análise a cada 5 minutos
*/5 * * * * cd /path/to/system-performance && uv run python src/main.py --brendan-analysis

# Iniciar API server no boot
@reboot cd /path/to/system-performance && uv run python src/brendan_api_server.py --port 8080
```

### 4. Com Docker Compose

```yaml
version: '3.8'

services:
  brendan-analyzer:
    build: .
    command: >
      sh -c "while true; do
        python src/main.py --brendan-analysis --verbose;
        sleep 300;
      done"
    volumes:
      - ./reports:/app/reports

  brendan-api:
    build: .
    command: python src/brendan_api_server.py --host 0.0.0.0 --port 8080
    ports:
      - "8080:8080"
    volumes:
      - ./reports:/app/reports
    depends_on:
      - brendan-analyzer

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    depends_on:
      - brendan-api
```

## 🎯 Casos de Uso

### 1. Monitoramento em Tempo Real

**Objetivo**: Visualizar insights de performance continuamente

**Setup**:
1. Executar análise a cada 5 minutos (cron ou while loop)
2. API server rodando persistentemente
3. Dashboard Grafana atualizado automaticamente (refresh 30s)

**Benefício**: Detecção rápida de problemas de performance

### 2. Análise Pós-Incidente

**Objetivo**: Revisar insights após um incidente

**Setup**:
1. Executar análise durante o incidente: `--brendan-analysis`
2. Relatórios salvos em `reports/`
3. Iniciar API server apontando para reports: `--reports-dir reports`
4. Revisar no Grafana

**Benefício**: Root cause analysis detalhada

### 3. Comparação de Ambientes

**Objetivo**: Comparar performance entre dev/staging/prod

**Setup**:
1. Executar análise em cada ambiente
2. API servers em portas diferentes (8080, 8081, 8082)
3. Dashboard Grafana com múltiplos data sources
4. Variáveis de template para selecionar ambiente

**Benefício**: Identificar diferenças de configuração/performance

### 4. Integração CI/CD

**Objetivo**: Gate de qualidade em deployments

**Setup**:
```yaml
# .github/workflows/performance-check.yml
- name: Run Performance Analysis
  run: uv run python src/main.py --brendan-analysis --verbose

- name: Check for Critical Issues
  run: |
    CRITICAL=$(curl -s http://localhost:8080/api/insights/severity/CRITICAL | jq '.count')
    if [ "$CRITICAL" -gt 0 ]; then
      echo "❌ Critical performance issues detected!"
      exit 1
    fi
```

**Benefício**: Prevenir deployments com problemas de performance

## 🔍 Troubleshooting

### API Server não Inicia

**Problema**: Erro ao iniciar API server

**Soluções**:
```bash
# Verificar se a porta já está em uso
lsof -i :8080

# Usar porta diferente
uv run python src/main.py --brendan-analysis --serve --api-port 8081

# Verificar logs
uv run python src/brendan_api_server.py --log-level DEBUG
```

### Grafana não Conecta à API

**Problema**: Dashboard não carrega dados

**Soluções**:
1. **Testar API manualmente**:
   ```bash
   curl http://localhost:8080/health
   ```

2. **Verificar data source**:
   - Configuration → Data Sources → Brendan Agent API
   - Clicar em "Save & Test"
   - Deve mostrar "Data source is working"

3. **Verificar CORS**:
   - Abrir DevTools no navegador
   - Verificar console por erros CORS
   - API já tem CORS habilitado, mas verifique firewall

### Dashboard Não Mostra Insights

**Problema**: Painéis vazios

**Causas e Soluções**:

1. **Nenhuma análise executada ainda**:
   ```bash
   uv run python src/main.py --brendan-analysis --verbose
   ```

2. **Nenhum insight detectado**:
   - Normal se sistema está saudável
   - Verifique `reports/brendan_cli_*.txt`

3. **API não encontra reports**:
   ```bash
   # Verificar se reports existem
   ls -la reports/validation_*.txt

   # Apontar para diretório correto
   uv run python src/brendan_api_server.py --reports-dir /caminho/correto
   ```

### JSON API Data Source não Disponível

**Problema**: Plugin JSON API não encontrado no Grafana

**Solução**:
```bash
# Instalar plugin
grafana-cli plugins install simpod-json-datasource

# Ou adicionar ao docker-compose.yml
environment:
  - GF_INSTALL_PLUGINS=simpod-json-datasource

# Reiniciar Grafana
docker-compose restart grafana
```

## 📚 Referências

### Arquivos Importantes

- **API Server**: `src/brendan_api_server.py`
- **CLI Integration**: `src/brendan_gregg_cli.py`
- **Main CLI**: `src/main.py`
- **Dashboard**: `grafana/dashboards/brendan-agent-analysis.json`
- **Persona**: `src/brendan_gregg_persona.py`

### Documentação Relacionada

- [Brendan Gregg Persona](BRENDAN_GREGG_PERSONA.md)
- [Validation System](BRENDAN_CLI_VALIDATION.md)
- [Quick Start](QUICKSTART_BRENDAN_PERSONA.md)
- [Architecture](ARCHITECTURE_BRENDAN_PERSONA.md)

### External Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Grafana JSON Data Source](https://grafana.com/docs/grafana/latest/datasources/json/)
- [Grafana SimpleJson Plugin](https://grafana.com/grafana/plugins/grafana-simple-json-datasource/)
- [Brendan Gregg's Blog](https://www.brendangregg.com/)

## 🎉 Resumo

✅ **API REST** implementada e testada
✅ **Dashboard Grafana** completo com múltiplos painéis
✅ **Integração CLI** com flags `--serve`, `--api-host`, `--api-port`
✅ **Documentação** completa com exemplos práticos
✅ **Troubleshooting** guide para problemas comuns

---

**Status**: ✅ COMPLETO E TESTADO
**Data**: 2025-10-28
**Versão**: 1.0.0
