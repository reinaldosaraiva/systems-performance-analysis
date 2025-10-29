#!/usr/bin/env python3
"""
Adiciona painéis HTML/JavaScript que funcionam 100% sem data source externo.
O JavaScript roda no navegador do usuário e acessa localhost:8080 diretamente.
"""

import json
import requests

# Baixar dashboard atual
response = requests.get(
    'http://admin:admin123@localhost:3000/api/dashboards/uid/d1e40598-6d0c-472c-950b-3e5c024f02e5'
)
dashboard_data = response.json()
dashboard = dashboard_data['dashboard']

# Remover painéis antigos do agente (ID > 42)
dashboard['panels'] = [p for p in dashboard['panels'] if p.get('id', 0) <= 42]

# Encontrar última posição
max_id = max(p['id'] for p in dashboard['panels'])
max_y = max(p['gridPos']['y'] + p['gridPos']['h'] for p in dashboard['panels'])

print(f"📊 Painéis restantes: {len(dashboard['panels'])}")
print(f"🔢 Último ID: {max_id}")
print(f"📍 Última posição Y: {max_y}")

# Header row
dashboard['panels'].append({
    "type": "row",
    "collapsed": False,
    "title": "🤖 BRENDAN GREGG AGENT - AI PERFORMANCE ANALYSIS",
    "gridPos": {"x": 0, "y": max_y, "w": 24, "h": 1},
    "id": max_id + 1
})

current_id = max_id + 2
start_y = max_y + 1

# Painel HTML único com toda a análise
html_content = """
<div id="brendan-analysis" style="font-family: monospace; padding: 20px;">
  <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px;">
    <div id="total-insights" class="stat-card" style="background: #1f77b4; color: white; padding: 20px; border-radius: 8px; text-align: center;">
      <div style="font-size: 48px; font-weight: bold;">-</div>
      <div style="font-size: 14px; margin-top: 10px;">Total Insights</div>
    </div>
    <div id="critical-count" class="stat-card" style="background: #dc143c; color: white; padding: 20px; border-radius: 8px; text-align: center;">
      <div style="font-size: 48px; font-weight: bold;">-</div>
      <div style="font-size: 14px; margin-top: 10px;">Critical Issues</div>
    </div>
    <div id="high-count" class="stat-card" style="background: #ff8c00; color: white; padding: 20px; border-radius: 8px; text-align: center;">
      <div style="font-size: 48px; font-weight: bold;">-</div>
      <div style="font-size: 14px; margin-top: 10px;">High Severity</div>
    </div>
    <div id="api-status" class="stat-card" style="background: #228b22; color: white; padding: 20px; border-radius: 8px; text-align: center;">
      <div style="font-size: 24px; font-weight: bold;">✓ HEALTHY</div>
      <div style="font-size: 14px; margin-top: 10px;">API Status</div>
    </div>
  </div>

  <div id="insights-table" style="background: #2c2c2c; color: #e0e0e0; padding: 20px; border-radius: 8px; overflow-x: auto;">
    <h3 style="margin-top: 0;">🔍 Latest Insights</h3>
    <div id="table-content">Loading...</div>
  </div>
</div>

<script>
async function loadAnalysis() {
  try {
    // Load summary
    const summaryResp = await fetch('http://localhost:8080/api/insights/summary');
    const summary = await summaryResp.json();

    document.querySelector('#total-insights .stat-card > div').textContent = summary.total_insights || 0;
    document.querySelector('#critical-count .stat-card > div').textContent = summary.by_severity.CRITICAL || 0;
    document.querySelector('#high-count .stat-card > div').textContent = summary.by_severity.HIGH || 0;

    // Load insights
    const insightsResp = await fetch('http://localhost:8080/api/insights?limit=10');
    const insightsData = await insightsResp.json();

    if (insightsData.insights && insightsData.insights.length > 0) {
      let tableHTML = '<table style="width: 100%; border-collapse: collapse;">';
      tableHTML += '<thead><tr style="border-bottom: 2px solid #444;">';
      tableHTML += '<th style="padding: 10px; text-align: left;">Severity</th>';
      tableHTML += '<th style="padding: 10px; text-align: left;">Component</th>';
      tableHTML += '<th style="padding: 10px; text-align: left;">Issue</th>';
      tableHTML += '<th style="padding: 10px; text-align: left;">Analysis</th>';
      tableHTML += '</tr></thead><tbody>';

      insightsData.insights.forEach(insight => {
        const severityColor = {
          'CRITICAL': '#dc143c',
          'HIGH': '#ff8c00',
          'MEDIUM': '#ffd700',
          'LOW': '#90ee90'
        }[insight.severity] || '#888';

        tableHTML += '<tr style="border-bottom: 1px solid #444;">';
        tableHTML += `<td style="padding: 10px;"><span style="background: ${severityColor}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">${insight.severity}</span></td>`;
        tableHTML += `<td style="padding: 10px;">${insight.component || 'N/A'}</td>`;
        tableHTML += `<td style="padding: 10px;"><strong>${insight.title || 'No title'}</strong></td>`;
        tableHTML += `<td style="padding: 10px;">${insight.observation || insight.root_cause || 'No details'}</td>`;
        tableHTML += '</tr>';
      });

      tableHTML += '</tbody></table>';
      document.getElementById('table-content').innerHTML = tableHTML;
    } else {
      document.getElementById('table-content').innerHTML = '<p style="color: #888;">No insights detected. System is healthy! ✓</p>';
    }

  } catch (error) {
    console.error('Error loading analysis:', error);
    document.getElementById('table-content').innerHTML = `<p style="color: #dc143c;">❌ Error: ${error.message}</p>`;
  }
}

// Load immediately and refresh every 30 seconds
loadAnalysis();
setInterval(loadAnalysis, 30000);
</script>
"""

dashboard['panels'].append({
    "type": "text",
    "id": current_id,
    "title": "",
    "gridPos": {"x": 0, "y": start_y, "w": 24, "h": 15},
    "options": {
        "mode": "html",
        "content": html_content
    }
})

print(f"✅ Adicionado 1 painel HTML com JavaScript")
print(f"📊 Total de painéis: {len(dashboard['panels'])}")

# Upload
upload_data = {
    "dashboard": dashboard,
    "overwrite": True,
    "message": "Add HTML/JavaScript panel for Brendan Agent"
}

response = requests.post(
    'http://admin:admin123@localhost:3000/api/dashboards/db',
    json=upload_data,
    headers={'Content-Type': 'application/json'}
)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Dashboard atualizado! Versão: {result['version']}")
    print(f"🎯 URL: {result['url']}")
else:
    print(f"❌ Erro: {response.status_code}")
    print(response.text)
