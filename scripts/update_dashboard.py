#!/usr/bin/env python3
"""
Script para atualizar dashboard no Grafana
"""

import json
import requests

# Load dashboard JSON
with open('grafana/dashboards/unified-use-method-dashboard.json', 'r') as f:
    dashboard_data = json.load(f)

# Add overwrite flag
dashboard_data['overwrite'] = True

# Grafana API endpoint
grafana_url = 'http://localhost:3000/api/dashboards/db'
auth = ('admin', 'admin123')

# Update dashboard
response = requests.post(
    grafana_url,
    auth=auth,
    headers={'Content-Type': 'application/json'},
    json=dashboard_data
)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Dashboard atualizado com sucesso!")
    print(f"   Status: {result.get('status')}")
    print(f"   Slug: {result.get('slug')}")
    print(f"   URL: {result.get('url')}")
else:
    print(f"❌ Erro ao atualizar dashboard: {response.status_code}")
    print(f"   {response.text}")
