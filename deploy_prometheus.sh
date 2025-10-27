#!/bin/bash

# Deploy Prometheus + Node Exporter para Análise Remota
# Uso: ./deploy_prometheus.sh [REMOTE_HOST] [USER]

set -e

REMOTE_HOST=${1:-"localhost"}
USER=${2:-"ubuntu"}
PROMETHEUS_PORT=9090
NODE_EXPORTER_PORT=9100

echo "🚀 Deploy Prometheus + Node Exporter para Análise Remota"
echo "📍 Host: $REMOTE_HOST"
echo "👤 Usuário: $USER"
echo "🔌 Prometheus Port: $PROMETHEUS_PORT"
echo "📊 Node Exporter Port: $NODE_EXPORTER_PORT"
echo ""

# Função para executar comandos remotos
remote_exec() {
    if [ "$REMOTE_HOST" = "localhost" ]; then
        bash -c "$1"
    else
        ssh -o StrictHostKeyChecking=no "$USER@$REMOTE_HOST" "$1"
    fi
}

# Função para copiar arquivos
remote_copy() {
    if [ "$REMOTE_HOST" = "localhost" ]; then
        cp "$1" "$2"
    else
        scp -o StrictHostKeyChecking=no "$1" "$USER@$REMOTE_HOST:$2"
    fi
}

echo "📦 Instalando dependências..."
remote_exec "
    sudo apt-get update
    sudo apt-get install -y wget curl systemd
"

echo "📥 Baixando Node Exporter..."
NODE_EXPORTER_VERSION="1.8.2"
remote_exec "
    cd /tmp
    wget -q https://github.com/prometheus/node_exporter/releases/download/v${NODE_EXPORTER_VERSION}/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
    tar xzf node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz
    sudo cp node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64/node_exporter /usr/local/bin/
    sudo chmod +x /usr/local/bin/node_exporter
    rm -rf node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64*
"

echo "🔧 Configurando Node Exporter como serviço..."
remote_exec "
    sudo tee /etc/systemd/system/node_exporter.service > /dev/null << 'EOF'
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter --web.listen-address=:$NODE_EXPORTER_PORT

[Install]
WantedBy=multi-user.target
EOF

    sudo useradd --no-create-home --shell /bin/false node_exporter 2>/dev/null || true
    sudo groupadd node_exporter 2>/dev/null || true
    sudo usermod -a -G node_exporter node_exporter 2>/dev/null || true
    sudo systemctl daemon-reload
    sudo systemctl enable node_exporter
    sudo systemctl start node_exporter
"

echo "📥 Baixando Prometheus..."
PROMETHEUS_VERSION="2.47.2"
remote_exec "
    cd /tmp
    wget -q https://github.com/prometheus/prometheus/releases/download/v${PROMETHEUS_VERSION}/prometheus-${PROMETHEUS_VERSION}.linux-amd64.tar.gz
    tar xzf prometheus-${PROMETHEUS_VERSION}.linux-amd64.tar.gz
    sudo mkdir -p /opt/prometheus
    sudo cp prometheus-${PROMETHEUS_VERSION}.linux-amd64/prometheus /opt/prometheus/
    sudo cp prometheus-${PROMETHEUS_VERSION}.linux-amd64/promtool /opt/prometheus/
    sudo cp -r prometheus-${PROMETHEUS_VERSION}.linux-amd64/consoles /opt/prometheus/
    sudo cp -r prometheus-${PROMETHEUS_VERSION}.linux-amd64/console_libraries /opt/prometheus/
    sudo mkdir -p /opt/prometheus/data
    sudo chown -R prometheus:prometheus /opt/prometheus 2>/dev/null || sudo chown -R \$USER:\$USER /opt/prometheus
    rm -rf prometheus-${PROMETHEUS_VERSION}.linux-amd64*
"

echo "🔧 Configurando Prometheus..."
PROMETHEUS_CONFIG="
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - \"first_rules.yml\"
  # - \"second_rules.yml\"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:$PROMETHEUS_PORT']

  - job_name: 'node_exporter'
    static_configs:
      - targets: ['localhost:$NODE_EXPORTER_PORT']
    scrape_interval: 5s
    metrics_path: /metrics
"

remote_exec "
    echo '$PROMETHEUS_CONFIG' | sudo tee /opt/prometheus/prometheus.yml > /dev/null
"

echo "🔧 Configurando Prometheus como serviço..."
remote_exec "
    sudo tee /etc/systemd/system/prometheus.service > /dev/null << 'EOF'
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/opt/prometheus/prometheus \\
    --config.file=/opt/prometheus/prometheus.yml \\
    --storage.tsdb.path=/opt/prometheus/data \\
    --web.console.libraries=/opt/prometheus/console_libraries \\
    --web.console.templates=/opt/prometheus/consoles \\
    --web.listen-address=0.0.0.0:$PROMETHEUS_PORT \\
    --web.enable-lifecycle

[Install]
WantedBy=multi-user.target
EOF

    sudo useradd --no-create-home --shell /bin/false prometheus 2>/dev/null || true
    sudo groupadd prometheus 2>/dev/null || true
    sudo usermod -a -G prometheus prometheus 2>/dev/null || true
    sudo systemctl daemon-reload
    sudo systemctl enable prometheus
    sudo systemctl start prometheus
"

echo "🔥 Configurando firewall (se necessário)..."
remote_exec "
    sudo ufw allow $PROMETHEUS_PORT/tcp 2>/dev/null || true
    sudo ufw allow $NODE_EXPORTER_PORT/tcp 2>/dev/null || true
    sudo iptables -C INPUT -p tcp --dport $PROMETHEUS_PORT -j ACCEPT 2>/dev/null || sudo iptables -I INPUT -p tcp --dport $PROMETHEUS_PORT -j ACCEPT
    sudo iptables -C INPUT -p tcp --dport $NODE_EXPORTER_PORT -j ACCEPT 2>/dev/null || sudo iptables -I INPUT -p tcp --dport $NODE_EXPORTER_PORT -j ACCEPT
"

echo "⏳ Aguardando serviços iniciarem..."
sleep 10

echo "🔍 Verificando status dos serviços..."
remote_exec "
    echo '=== Node Exporter Status ==='
    sudo systemctl status node_exporter --no-pager -l
    echo ''
    echo '=== Prometheus Status ==='
    sudo systemctl status prometheus --no-pager -l
    echo ''
    echo '=== Verificando portas ==='
    netstat -tlnp | grep -E '($PROMETHEUS_PORT|$NODE_EXPORTER_PORT)' || ss -tlnp | grep -E '($PROMETHEUS_PORT|$NODE_EXPORTER_PORT)'
    echo ''
    echo '=== Testando Node Exporter ==='
    curl -s http://localhost:$NODE_EXPORTER_PORT/metrics | head -5
    echo ''
    echo '=== Testando Prometheus ==='
    curl -s http://localhost:$PROMETHEUS_PORT/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health, lastError: .lastError}' 2>/dev/null || echo 'Prometheus API responding'
"

echo ""
echo "✅ Deploy concluído!"
echo ""
echo "🌐 URLs de acesso:"
if [ "$REMOTE_HOST" = "localhost" ]; then
    echo "   Prometheus: http://localhost:$PROMETHEUS_PORT"
    echo "   Node Exporter: http://localhost:$NODE_EXPORTER_PORT/metrics"
else
    echo "   Prometheus: http://$REMOTE_HOST:$PROMETHEUS_PORT"
    echo "   Node Exporter: http://$REMOTE_HOST:$NODE_EXPORTER_PORT/metrics"
fi
echo ""
echo "🔧 Para testar a análise:"
echo "   python prometheus_analyzer.py --prometheus-url http://$REMOTE_HOST:$PROMETHEUS_PORT"
echo ""
echo "🔄 Para modo daemon (a cada 5 minutos):"
echo "   python prometheus_analyzer.py --prometheus-url http://$REMOTE_HOST:$PROMETHEUS_PORT --daemon"
echo ""
echo "📊 Para análise contínua:"
echo "   python prometheus_analyzer.py --prometheus-url http://$REMOTE_HOST:$PROMETHEUS_PORT --continuous"