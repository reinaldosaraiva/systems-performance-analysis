#!/usr/bin/env python3
"""
Script para adicionar painéis do agente Brendan Gregg usando Infinity data source.
"""

import json

def add_brendan_panels_v2():
    # Ler dashboard atual
    with open('/tmp/current_dashboard.json', 'r') as f:
        dashboard_data = json.load(f)

    dashboard = dashboard_data['dashboard']

    # UID do data source Infinity
    datasource_uid = "ff7b1bf4-30c3-4663-9292-fca541b51ad4"

    # Encontrar último ID e última posição Y
    max_id = max(p['id'] for p in dashboard['panels'])
    max_y = max(p['gridPos']['y'] + p['gridPos']['h'] for p in dashboard['panels'])

    print(f"📊 Dashboard atual: {len(dashboard['panels'])} painéis")
    print(f"🔢 Último ID: {max_id}")
    print(f"📍 Última posição Y: {max_y}")

    # Remover painéis antigos do agente se existirem (IDs > 42)
    dashboard['panels'] = [p for p in dashboard['panels'] if p['id'] <= 42]
    print(f"🧹 Limpeza: {len(dashboard['panels'])} painéis restantes")

    # Criar seção de header
    brendan_section = {
        "type": "row",
        "collapsed": False,
        "title": "🤖 BRENDAN GREGG AGENT - AI PERFORMANCE ANALYSIS",
        "gridPos": {"x": 0, "y": max_y, "w": 24, "h": 1},
        "id": max_id + 1,
        "panels": []
    }

    dashboard['panels'].append(brendan_section)

    start_y = max_y + 1
    current_id = max_id + 2

    # PAINEL 1: Total Insights (usando text simples do endpoint)
    dashboard['panels'].append({
        "datasource": {
            "type": "grafana-infinity-datasource",
            "uid": datasource_uid
        },
        "type": "stat",
        "id": current_id,
        "title": "🤖 AI Agent - Total Insights",
        "gridPos": {"x": 0, "y": start_y, "w": 6, "h": 4},
        "targets": [{
            "datasource": {
                "type": "grafana-infinity-datasource",
                "uid": datasource_uid
            },
            "refId": "A",
            "type": "json",
            "source": "url",
            "format": "table",
            "url": "http://localhost:8080/api/insights/summary",
            "url_options": {
                "method": "GET"
            }
        }],
        "options": {
            "colorMode": "value",
            "graphMode": "area",
            "justifyMode": "auto",
            "orientation": "auto",
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"],
                "fields": "total_insights"
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

    # PAINEL 2: Critical Issues Count
    dashboard['panels'].append({
        "datasource": {
            "type": "grafana-infinity-datasource",
            "uid": datasource_uid
        },
        "type": "stat",
        "id": current_id,
        "title": "🤖 AI Agent - Critical Issues",
        "gridPos": {"x": 6, "y": start_y, "w": 6, "h": 4},
        "targets": [{
            "datasource": {
                "type": "grafana-infinity-datasource",
                "uid": datasource_uid
            },
            "refId": "A",
            "type": "json",
            "source": "url",
            "format": "table",
            "url": "http://localhost:8080/api/insights/severity/CRITICAL",
            "url_options": {
                "method": "GET"
            }
        }],
        "options": {
            "colorMode": "background",
            "graphMode": "none",
            "justifyMode": "center",
            "orientation": "auto",
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"],
                "fields": "count"
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

    # PAINEL 3: High Severity Count
    dashboard['panels'].append({
        "datasource": {
            "type": "grafana-infinity-datasource",
            "uid": datasource_uid
        },
        "type": "stat",
        "id": current_id,
        "title": "🤖 AI Agent - High Severity",
        "gridPos": {"x": 12, "y": start_y, "w": 6, "h": 4},
        "targets": [{
            "datasource": {
                "type": "grafana-infinity-datasource",
                "uid": datasource_uid
            },
            "refId": "A",
            "type": "json",
            "source": "url",
            "format": "table",
            "url": "http://localhost:8080/api/insights/severity/HIGH",
            "url_options": {
                "method": "GET"
            }
        }],
        "options": {
            "colorMode": "background",
            "graphMode": "none",
            "justifyMode": "center",
            "orientation": "auto",
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"],
                "fields": "count"
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

    # PAINEL 4: API Health Status
    dashboard['panels'].append({
        "datasource": {
            "type": "grafana-infinity-datasource",
            "uid": datasource_uid
        },
        "type": "stat",
        "id": current_id,
        "title": "🤖 AI Agent - API Status",
        "gridPos": {"x": 18, "y": start_y, "w": 6, "h": 4},
        "targets": [{
            "datasource": {
                "type": "grafana-infinity-datasource",
                "uid": datasource_uid
            },
            "refId": "A",
            "type": "json",
            "source": "url",
            "format": "table",
            "url": "http://localhost:8080/health",
            "url_options": {
                "method": "GET"
            }
        }],
        "options": {
            "colorMode": "background",
            "graphMode": "none",
            "justifyMode": "center",
            "orientation": "auto",
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"],
                "fields": "status"
            },
            "textMode": "value"
        },
        "fieldConfig": {
            "defaults": {
                "mappings": [
                    {
                        "type": "value",
                        "options": {
                            "healthy": {
                                "text": "✓ HEALTHY",
                                "color": "green"
                            }
                        }
                    }
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

    # PAINEL 5: Insights Table
    dashboard['panels'].append({
        "datasource": {
            "type": "grafana-infinity-datasource",
            "uid": datasource_uid
        },
        "type": "table",
        "id": current_id,
        "title": "🤖 AI Agent - Latest Insights (Detailed Analysis)",
        "gridPos": {"x": 0, "y": start_y + 4, "w": 24, "h": 8},
        "targets": [{
            "datasource": {
                "type": "grafana-infinity-datasource",
                "uid": datasource_uid
            },
            "refId": "A",
            "type": "json",
            "source": "url",
            "format": "table",
            "url": "http://localhost:8080/api/insights?limit=10",
            "url_options": {
                "method": "GET"
            },
            "root_selector": "insights"
        }],
        "transformations": [],
        "options": {
            "showHeader": True,
            "sortBy": []
        },
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "align": "left",
                    "displayMode": "auto",
                    "inspect": False
                }
            },
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "severity"},
                    "properties": [
                        {
                            "id": "custom.displayMode",
                            "value": "color-background"
                        },
                        {
                            "id": "mappings",
                            "value": [
                                {"type": "value", "value": "CRITICAL", "options": {"CRITICAL": {"color": "red", "text": "🔴 CRITICAL"}}},
                                {"type": "value", "value": "HIGH", "options": {"HIGH": {"color": "orange", "text": "🟠 HIGH"}}},
                                {"type": "value", "value": "MEDIUM", "options": {"MEDIUM": {"color": "yellow", "text": "🟡 MEDIUM"}}},
                                {"type": "value", "value": "LOW", "options": {"LOW": {"color": "green", "text": "🟢 LOW"}}}
                            ]
                        }
                    ]
                },
                {
                    "matcher": {"id": "byName", "options": "component"},
                    "properties": [
                        {
                            "id": "custom.displayMode",
                            "value": "color-background"
                        }
                    ]
                }
            ]
        }
    })
    current_id += 1

    print(f"✅ Adicionados {current_id - max_id - 1} novos painéis do agente Brendan Gregg")
    print(f"📊 Total de painéis agora: {len(dashboard['panels'])}")

    # Preparar para upload
    upload_data = {
        "dashboard": dashboard,
        "overwrite": True,
        "message": "Add Brendan Gregg AI Agent panels with Infinity datasource"
    }

    # Salvar
    with open('/tmp/updated_dashboard_v2.json', 'w') as f:
        json.dump(upload_data, f, indent=2)

    print("✅ Dashboard atualizado salvo em /tmp/updated_dashboard_v2.json")
    print(f"📦 Data source UID: {datasource_uid}")
    return True

if __name__ == "__main__":
    try:
        add_brendan_panels_v2()
        print("\n🎯 Próximo passo: Executar upload do dashboard")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
