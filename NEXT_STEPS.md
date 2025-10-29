# 🚀 PRÓXIMOS PASSOS - Otimização Multi-Agente

## 📅 Para Amanhã

---

## 🎯 OBJETIVO PRINCIPAL: Reduzir Latência de 70s para ~15s

### Problema Atual:
- **Tempo atual:** 70 segundos (6 chamadas sequenciais)
- **Gargalo:** Agentes executam sequencialmente (um por vez)
- **Solução:** Usar `asyncio.gather()` para execução paralela

### Benefício Esperado:
- **Tempo esperado:** 10-15 segundos (6 chamadas paralelas)
- **Ganho:** 5x mais rápido!

---

## 📋 TAREFA 1: Paralelizar Chamadas dos Agentes

### Arquivo: `src/infrastructure/ai/autogen_multiagent.py`

### Mudança:

#### Antes (Sequencial - 70s):
```python
for agent in self.agents:
    logger.info(f"Calling agent: {agent['name']}")
    response = await self._call_ollama(prompt)
    agent_analyses.append({...})
```

#### Depois (Paralelo - 15s):
```python
import asyncio

# Criar tasks para todos os agentes
async def call_agent(agent):
    prompt = f"""{agent['system_message']}

Scenario: {context}

Analyze from your {agent['role']} perspective."""

    try:
        response = await self._call_ollama(prompt)
        return {
            "agent": agent["name"],
            "role": agent["role"],
            "analysis": response
        }
    except Exception as e:
        logger.error(f"Error calling agent {agent['name']}: {e}")
        return None

# Executar todos em paralelo
tasks = [call_agent(agent) for agent in self.agents]
results = await asyncio.gather(*tasks, return_exceptions=True)

# Filtrar resultados válidos
agent_analyses = [r for r in results if r is not None and not isinstance(r, Exception)]
```

### Passos:
1. ✅ Importar `asyncio`
2. ✅ Criar função `call_agent()` async
3. ✅ Usar `asyncio.gather()` para executar tudo junto
4. ✅ Filtrar exceções com `return_exceptions=True`
5. ✅ Testar e validar tempo

---

## 📋 TAREFA 2: Adicionar Timeout por Agente

### Problema:
Se um agente travar, não deve bloquear os outros

### Solução:
```python
import asyncio

async def call_agent_with_timeout(agent, timeout=30):
    """Call agent with timeout protection."""
    try:
        return await asyncio.wait_for(
            call_agent(agent),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning(f"Agent {agent['name']} timed out after {timeout}s")
        return None

# Uso:
tasks = [call_agent_with_timeout(agent, timeout=30) for agent in self.agents]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

### Benefício:
- Agentes lentos não bloqueiam os rápidos
- Sistema mais resiliente
- Melhor experiência do usuário

---

## 📋 TAREFA 3: Otimizar Consolidação

### Opção A: Consolidar enquanto agentes rodam
```python
# Assim que 3+ agentes responderem, começar consolidação
# Não esperar todos os 5

async def smart_consolidation(agent_analyses, min_agents=3):
    """Start consolidation as soon as we have minimum agents."""
    if len(agent_analyses) >= min_agents:
        return await self._consolidate_analyses(agent_analyses, context)
    else:
        return self._create_fallback_consolidated_insight(agent_analyses)
```

### Opção B: Consolidação paralela
```python
# Enquanto último agente responde, já processar os anteriores
consolidation_task = asyncio.create_task(
    self._consolidate_analyses(agent_analyses[:4], context)
)
last_agent = await call_agent(self.agents[4])
consolidated = await consolidation_task
```

---

## 📋 TAREFA 4: Caching Inteligente

### Implementar Cache Redis/Memória

```python
import hashlib
from typing import Optional

class CachedAutoGenMultiAgent(AutoGenMultiAgent):
    def __init__(self, *args, cache_ttl=300, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}  # Ou Redis
        self.cache_ttl = cache_ttl  # 5 minutos

    def _generate_cache_key(self, context: str) -> str:
        """Generate cache key from context."""
        return hashlib.md5(context.encode()).hexdigest()

    async def analyze_collaborative(
        self,
        metrics: Optional[SystemMetrics] = None,
        max_rounds: int = 2,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Analyze with caching support."""

        context = self._build_analysis_context(metrics)
        cache_key = self._generate_cache_key(context)

        # Check cache
        if use_cache and cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['timestamp'] < self.cache_ttl:
                logger.info("Returning cached analysis")
                return cached['result']

        # Normal analysis
        result = await super().analyze_collaborative(metrics, max_rounds)

        # Store in cache
        self.cache[cache_key] = {
            'timestamp': time.time(),
            'result': result
        }

        return result
```

### Benefício:
- Análises idênticas retornam instantaneamente
- Reduz custos de chamadas LLM
- Melhor para dashboards com refresh frequente

---

## 📋 TAREFA 5: Métricas e Observabilidade

### Adicionar métricas de performance:

```python
import time
from dataclasses import dataclass

@dataclass
class AgentMetrics:
    agent_name: str
    duration: float
    response_size: int
    success: bool
    error: Optional[str] = None

class InstrumentedAutoGenMultiAgent(AutoGenMultiAgent):
    async def call_agent_with_metrics(self, agent) -> tuple[dict, AgentMetrics]:
        """Call agent and collect metrics."""
        start = time.time()

        try:
            result = await call_agent(agent)
            duration = time.time() - start

            metrics = AgentMetrics(
                agent_name=agent['name'],
                duration=duration,
                response_size=len(result['analysis']),
                success=True
            )

            return result, metrics
        except Exception as e:
            duration = time.time() - start
            metrics = AgentMetrics(
                agent_name=agent['name'],
                duration=duration,
                response_size=0,
                success=False,
                error=str(e)
            )
            return None, metrics

    async def analyze_collaborative(self, ...):
        """Enhanced analysis with metrics."""
        tasks = [self.call_agent_with_metrics(agent) for agent in self.agents]
        results = await asyncio.gather(*tasks)

        # Separate results and metrics
        analyses = [r[0] for r in results if r[0] is not None]
        metrics = [r[1] for r in results]

        # Log metrics
        for m in metrics:
            logger.info(f"Agent {m.agent_name}: {m.duration:.2f}s, "
                       f"size={m.response_size}, success={m.success}")

        # Continue with consolidation...
```

---

## 📋 TAREFA 6: Estratégia de Fallback Progressivo

### Níveis de qualidade baseados em quantos agentes responderam:

```python
async def adaptive_consolidation(agent_analyses, context):
    """Adapt quality based on number of agents."""

    num_agents = len(agent_analyses)

    if num_agents >= 5:
        # Todos responderam - análise completa
        confidence = 95
        quality = "excellent"
    elif num_agents >= 3:
        # Maioria respondeu - análise boa
        confidence = 88
        quality = "good"
    elif num_agents >= 2:
        # Mínimo respondeu - análise básica
        confidence = 80
        quality = "basic"
    else:
        # Só 1 ou nenhum - fallback
        return self._create_fallback_consolidated_insight(agent_analyses)

    # Consolidar com qualidade adaptativa
    insights = await self._consolidate_analyses(agent_analyses, context)

    # Ajustar confidence baseado em quantos agentes participaram
    for insight in insights:
        insight['confidence'] = confidence
        insight['quality'] = quality
        insight['agents_participated'] = num_agents

    return insights
```

---

## 📊 COMPARAÇÃO ESPERADA

### Antes (Atual):
```
Single-Agent:    ~7 segundos  (85% confidence)
Multi-Agent:    ~70 segundos  (92% confidence)
```

### Depois (Otimizado):
```
Single-Agent:    ~7 segundos  (85% confidence)
Multi-Agent:    ~15 segundos  (92% confidence)  ← 5x mais rápido!
Multi-Agent (cached): <1 segundo  (92% confidence)
```

---

## 🎯 ORDEM DE IMPLEMENTAÇÃO RECOMENDADA

### Dia 1 (Amanhã):
1. ✅ **TAREFA 1**: Paralelizar agentes com `asyncio.gather()` (PRIORIDADE ALTA)
   - Impacto: 70s → 15s (5x mais rápido)
   - Complexidade: Média
   - Tempo estimado: 1-2 horas

2. ✅ **TAREFA 2**: Adicionar timeout por agente
   - Impacto: Resiliência
   - Complexidade: Baixa
   - Tempo estimado: 30 minutos

3. ✅ **TAREFA 5**: Métricas básicas
   - Impacto: Observabilidade
   - Complexidade: Baixa
   - Tempo estimado: 30 minutos

### Dia 2 (Depois):
4. ✅ **TAREFA 4**: Caching (Redis ou memória)
   - Impacto: 15s → <1s para análises repetidas
   - Complexidade: Média
   - Tempo estimado: 2-3 horas

5. ✅ **TAREFA 3**: Consolidação inteligente
   - Impacto: -2s adicional
   - Complexidade: Média
   - Tempo estimado: 1 hora

6. ✅ **TAREFA 6**: Fallback progressivo
   - Impacto: Melhor UX
   - Complexidade: Baixa
   - Tempo estimado: 1 hora

---

## 📝 CÓDIGO DE EXEMPLO COMPLETO (TAREFA 1)

### Arquivo: `src/infrastructure/ai/autogen_multiagent.py`

```python
async def analyze_collaborative(
    self,
    metrics: Optional[SystemMetrics] = None,
    max_rounds: int = 2
) -> Dict[str, Any]:
    """Run collaborative analysis with all agents (PARALLEL)."""

    logger.info(f"Starting PARALLEL analysis with {len(self.agents)} agents")

    try:
        # Build analysis context
        context = self._build_analysis_context(metrics)

        # Define async function to call each agent
        async def call_single_agent(agent):
            """Call a single agent with error handling."""
            logger.info(f"Calling agent: {agent['name']}")

            try:
                # Create agent-specific prompt
                prompt = f"""{agent['system_message']}

Scenario: {context}

Analyze from your {agent['role']} perspective and provide 2-3 actionable recommendations.
Respond with JSON only."""

                # Call Ollama
                response = await self._call_ollama(prompt)

                logger.info(f"Agent {agent['name']} completed ({len(response)} chars)")

                return {
                    "agent": agent["name"],
                    "role": agent["role"],
                    "analysis": response
                }

            except Exception as e:
                logger.error(f"Error calling agent {agent['name']}: {e}")
                return None

        # Execute all agents in PARALLEL using asyncio.gather()
        logger.info("Executing all agents in PARALLEL...")
        start_time = time.time()

        tasks = [call_single_agent(agent) for agent in self.agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        duration = time.time() - start_time
        logger.info(f"All agents completed in {duration:.2f}s")

        # Filter valid results
        agent_analyses = []
        for result in results:
            if result is not None and not isinstance(result, Exception):
                agent_analyses.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Agent failed with exception: {result}")

        logger.info(f"Successfully collected {len(agent_analyses)}/{len(self.agents)} agent analyses")

        # Consolidate all analyses into final insights
        insights = await self._consolidate_analyses(agent_analyses, context)

        logger.info(f"Collaborative analysis completed with {len(insights)} insights")

        return {
            "status": "success",
            "agents_participated": len(agent_analyses),
            "execution_time": f"{duration:.2f}s",
            "rounds": 1,
            "insights": insights,
            "collaboration_summary": f"Parallel analysis from {len(agent_analyses)} specialized agents"
        }

    except Exception as e:
        logger.error(f"Error in collaborative analysis: {e}")
        return {
            "status": "error",
            "error": str(e),
            "insights": []
        }
```

---

## ✅ CHECKLIST PARA AMANHÃ

### Setup:
- [ ] Abrir projeto no editor
- [ ] Ativar ambiente virtual: `source .venv/bin/activate`
- [ ] Verificar Ollama rodando: `curl http://localhost:11434/api/version`

### Implementação:
- [ ] TAREFA 1: Paralelizar agentes com `asyncio.gather()`
- [ ] Adicionar import `import asyncio` no topo
- [ ] Criar função `call_single_agent()` async
- [ ] Substituir loop `for` por `asyncio.gather()`
- [ ] Testar localmente (deve reduzir de 70s para ~15s)

### Testes:
- [ ] Rebuild Docker: `docker compose build brendan-api`
- [ ] Restart: `docker compose up -d brendan-api`
- [ ] Testar endpoint: `time curl -s http://localhost:8080/api/insights/autogen`
- [ ] Verificar tempo (esperado: 10-20s)
- [ ] Verificar logs: `docker compose logs brendan-api | grep "completed in"`

### Validação:
- [ ] Comparar tempo antes (70s) vs depois (15s)
- [ ] Verificar qualidade dos insights (deve manter 92% confidence)
- [ ] Confirmar que todos os 5 agentes estão participando
- [ ] Testar múltiplas chamadas para validar consistência

### Commit:
- [ ] `git add src/infrastructure/ai/autogen_multiagent.py`
- [ ] `git commit -m "perf: parallelize multi-agent calls with asyncio (70s→15s)"`
- [ ] `git log --oneline -1` (verificar)

---

## 🎯 RESULTADO ESPERADO

**Antes:**
```bash
$ time curl -s http://localhost:8080/api/insights/autogen
real    1m10.76s  # 70 segundos
```

**Depois:**
```bash
$ time curl -s http://localhost:8080/api/insights/autogen
real    0m15.23s  # 15 segundos (5x mais rápido!)
```

---

## 📚 REFERÊNCIAS

### Asyncio Documentation:
- https://docs.python.org/3/library/asyncio-task.html
- `asyncio.gather()` - Run tasks concurrently
- `asyncio.wait_for()` - Add timeout to coroutine
- `asyncio.create_task()` - Schedule coroutine

### Código Similar:
- `src/infrastructure/ai/ollama_llm_client.py` - Já usa httpx async
- `src/application/use_cases/performance/get_autogen_insights.py` - Use case async

---

## 💡 DICAS

1. **Teste localmente primeiro** antes do Docker
2. **Use logs** para debugar timing: `logger.info(f"Agent {name} took {duration}s")`
3. **Comece simples** - asyncio.gather() básico antes de otimizações avançadas
4. **Valide a qualidade** - garantir que paralelização não afeta resultado
5. **Monitore memória** - 6 chamadas simultâneas ao Ollama consomem mais RAM

---

## 🚀 BONUS: Otimização Extrema (Futuro)

Se quiser ir além de 15s → 10s:

### Streaming Responses:
```python
# Em vez de aguardar resposta completa, processar streaming
async for chunk in ollama_stream(prompt):
    partial_analysis += chunk
    # Começar consolidação com análises parciais
```

### Modelos Menores para Agentes:
```python
# Usar modelo menor/mais rápido para agentes individuais
agent_model = "mistral:7b"  # Mais rápido
consolidator_model = "minimax-m2:cloud"  # Mais poderoso
```

### Connection Pooling:
```python
# Reutilizar conexões HTTP
self.client = httpx.AsyncClient(
    timeout=120,
    limits=httpx.Limits(max_connections=10)
)
```

---

**Boa sorte amanhã! 🚀**

**Meta:** Reduzir de 70s para 15s com `asyncio.gather()` ✨
