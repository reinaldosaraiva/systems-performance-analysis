#!/usr/bin/env python3
"""
Script para adicionar painéis do agente Brendan Gregg ao dashboard USE Method existente.
"""

import json
import sys

def add_brendan_panels():
    # Ler dashboard atual
    with open('/tmp/current_dashboard.json', 'r') as f:
        dashboard_data = json.load(f)

    dashboard = dashboard_data['dashboard']

    # Encontrar último ID e última posição Y
    max_id = max(p['id'] for p in dashboard['panels'])
    max_y = max(p['gridPos']['y'] + p['gridPos']['h'] for p in dashboard['panels'])

    print(f"📊 Dashboard atual: {len(dashboard['panels'])} painéis")
    print(f"🔢 Último ID: {max_id}")
    print(f"📍 Última posição Y: {max_y}")

    # Criar seção de header para os painéis do agente
    brendan_section = {
        "type": "row",
        "collapsed": False,
        "title": "🤖 BRENDAN GREGG AGENT - AI PERFORMANCE ANALYSIS",
        "gridPos": {"x": 0, "y": max_y, "w": 24, "h": 1},
        "id": max_id + 1,
        "panels": []
    }

    # Adicionar seção header
    dashboard['panels'].append(brendan_section)

    start_y = max_y + 1
    current_id = max_id + 2

    # PAINEL 1: Total Insights
    dashboard['panels'].append({
        "type": "stat",
        "id": current_id,
        "title": "AI Agent - Total Insights",
        "gridPos": {"x": 0, "y": start_y, "w": 6, "h": 4},
        "targets": [{
            "refId": "A",
            "url": "http://localhost:8080/api/insights/summary",
            "format": "json"
        }],
        "options": {
            "colorMode": "value",
            "graphMode": "area",
            "justifyMode": "auto",
            "orientation": "auto",
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"],
                "fields": "/^total_insights$/"
            },
            "textMode": "auto"
        },
        "fieldConfig": {
            "defaults": {
                "mappings": [],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 3},
                        {"color": "red", "value": 5}
                    ]
                },
                "unit": "short"
            }
        }
    })
    current_id += 1

    # PAINEL 2: Critical Issues
    dashboard['panels'].append({
        "type": "stat",
        "id": current_id,
        "title": "AI Agent - Critical Issues",
        "gridPos": {"x": 6, "y": start_y, "w": 6, "h": 4},
        "targets": [{
            "refId": "A",
            "url": "http://localhost:8080/api/insights/severity/CRITICAL",
            "format": "json"
        }],
        "options": {
            "colorMode": "background",
            "graphMode": "none",
            "justifyMode": "center",
            "orientation": "auto",
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"],
                "fields": "/^count$/"
            },
            "textMode": "value_and_name"
        },
        "fieldConfig": {
            "defaults": {
                "mappings": [],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "red", "value": 1}
                    ]
                },
                "unit": "short"
            }
        }
    })
    current_id += 1

    # PAINEL 3: High Severity
    dashboard['panels'].append({
        "type": "stat",
        "id": current_id,
        "title": "AI Agent - High Severity",
        "gridPos": {"x": 12, "y": start_y, "w": 6, "h": 4},
        "targets": [{
            "refId": "A",
            "url": "http://localhost:8080/api/insights/severity/HIGH",
            "format": "json"
        }],
        "options": {
            "colorMode": "background",
            "graphMode": "none",
            "justifyMode": "center",
            "orientation": "auto",
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"],
                "fields": "/^count$/"
            },
            "textMode": "value_and_name"
        },
        "fieldConfig": {
            "defaults": {
                "mappings": [],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "orange", "value": 1}
                    ]
                },
                "unit": "short"
            }
        }
    })
    current_id += 1

    # PAINEL 4: API Health
    dashboard['panels'].append({
        "type": "stat",
        "id": current_id,
        "title": "AI Agent - API Status",
        "gridPos": {"x": 18, "y": start_y, "w": 6, "h": 4},
        "targets": [{
            "refId": "A",
            "url": "http://localhost:8080/health",
            "format": "json"
        }],
        "options": {
            "colorMode": "background",
            "graphMode": "none",
            "justifyMode": "center",
            "orientation": "auto",
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"],
                "fields": "/^status$/"
            },
            "textMode": "value"
        },
        "fieldConfig": {
            "defaults": {
                "mappings": [
                    {"type": "value", "options": {"healthy": {"text": "✓ HEALTHY", "color": "green"}}}
                ],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None}
                    ]
                }
            }
        }
    })
    current_id += 1

    # PAINEL 5: Latest Insight (Tabela/Text)
    dashboard['panels'].append({
        "type": "table",
        "id": current_id,
        "title": "🤖 AI Agent - Latest Insights (Detailed Analysis)",
        "gridPos": {"x": 0, "y": start_y + 4, "w": 24, "h": 8},
        "targets": [{
            "refId": "A",
            "url": "http://localhost:8080/api/insights?limit=10",
            "format": "json"
        }],
        "transformations": [
            {
                "id": "filterFieldsByName",
                "options": {
                    "include": {
                        "names": ["insights[0].timestamp", "insights[0].severity", "insights[0].component",
                                "insights[0].title", "insights[0].observation", "insights[0].root_cause",
                                "insights[0].immediate_action"]
                    }
                }
            }
        ],
        "options": {
            "showHeader": True,
            "sortBy": []
        },
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "align": "auto",
                    "displayMode": "auto",
                    "inspect": False
                }
            },
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "insights[0].severity"},
                    "properties": [
                        {
                            "id": "custom.displayMode",
                            "value": "color-background"
                        },
                        {
                            "id": "mappings",
                            "value": [
                                {"type": "value", "value": "CRITICAL", "color": "red"},
                                {"type": "value", "value": "HIGH", "color": "orange"},
                                {"type": "value", "value": "MEDIUM", "color": "yellow"},
                                {"type": "value", "value": "LOW", "color": "green"}
                            ]
                        },
                        {
                            "id": "displayName",
                            "value": "Severity"
                        }
                    ]
                },
                {
                    "matcher": {"id": "byName", "options": "insights[0].component"},
                    "properties": [
                        {
                            "id": "displayName",
                            "value": "Component"
                        }
                    ]
                },
                {
                    "matcher": {"id": "byName", "options": "insights[0].title"},
                    "properties": [
                        {
                            "id": "displayName",
                            "value": "Issue Detected"
                        }
                    ]
                },
                {
                    "matcher": {"id": "byName", "options": "insights[0].observation"},
                    "properties": [
                        {
                            "id": "displayName",
                            "value": "Analysis"
                        }
                    ]
                },
                {
                    "matcher": {"id": "byName", "options": "insights[0].root_cause"},
                    "properties": [
                        {
                            "id": "displayName",
                            "value": "Root Cause"
                        }
                    ]
                },
                {
                    "matcher": {"id": "byName", "options": "insights[0].immediate_action"},
                    "properties": [
                        {
                            "id": "displayName",
                            "value": "Recommended Action"
                        }
                    ]
                }
            ]
        }
    })
    current_id += 1

    print(f"✅ Adicionados {current_id - max_id - 1} novos painéis do agente Brendan Gregg")
    print(f"📊 Total de painéis agora: {len(dashboard['panels'])}")

    # Preparar para upload (remover campos meta)
    upload_data = {
        "dashboard": dashboard,
        "overwrite": True,
        "message": "Add Brendan Gregg AI Agent panels"
    }

    # Salvar para upload
    with open('/tmp/updated_dashboard.json', 'w') as f:
        json.dump(upload_data, f, indent=2)

    print("✅ Dashboard atualizado salvo em /tmp/updated_dashboard.json")
    return True

if __name__ == "__main__":
    try:
        add_brendan_panels()
        print("\n🎯 Próximo passo: Executar upload do dashboard")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
