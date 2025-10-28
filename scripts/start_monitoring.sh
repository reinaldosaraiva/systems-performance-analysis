#!/bin/bash
# Systems Performance Monitoring Stack
# Script para iniciar o ambiente completo de monitoramento

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir banners
print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║         Systems Performance Monitoring Stack              ║"
    echo "║              Docker Compose Environment                   ║"
    echo "║              Based on Brendan Gregg USE Method             ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Função para verificar dependências
check_dependencies() {
    echo -e "${YELLOW}🔍 Checking dependencies...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Dependencies OK${NC}"
}

# Função para criar diretórios necessários
create_directories() {
    echo -e "${YELLOW}📁 Creating necessary directories...${NC}"
    
    mkdir -p logs
    mkdir -p data/{prometheus,grafana,victoria,alertmanager,redis}
    mkdir -p exports
    mkdir -p backups
    
    echo -e "${GREEN}✅ Directories created${NC}"
}

# Função para configurar permissões
setup_permissions() {
    echo -e "${YELLOW}🔐 Setting up permissions...${NC}"
    
    # Permissões para volumes do Docker
    sudo chown -R 472:472 data/grafana 2>/dev/null || true
    sudo chown -R 65534:65534 data/prometheus 2>/dev/null || true
    sudo chown -R 1000:1000 data/victoria 2>/dev/null || true
    
    echo -e "${GREEN}✅ Permissions configured${NC}"
}

# Função para iniciar serviços
start_services() {
    echo -e "${YELLOW}🚀 Starting monitoring services...${NC}"
    
    # Inicia na ordem correta
    docker compose up -d redis victoria-metrics
    
    echo -e "${BLUE}⏳ Waiting for VictoriaMetrics...${NC}"
    sleep 10
    
    docker compose up -d prometheus alertmanager
    
    echo -e "${BLUE}⏳ Waiting for Prometheus...${NC}"
    sleep 15
    
    docker compose up -d grafana node-exporter
    
    echo -e "${BLUE}⏳ Waiting for Grafana...${NC}"
    sleep 10
    
    echo -e "${GREEN}✅ All services started${NC}"
}

# Função para verificar saúde dos serviços
check_health() {
    echo -e "${YELLOW}🏥 Checking service health...${NC}"
    
    # Prometheus
    if curl -s http://localhost:9090/-/healthy > /dev/null; then
        echo -e "${GREEN}✅ Prometheus: Healthy${NC}"
    else
        echo -e "${RED}❌ Prometheus: Unhealthy${NC}"
    fi
    
    # Grafana
    if curl -s http://localhost:3000/api/health > /dev/null; then
        echo -e "${GREEN}✅ Grafana: Healthy${NC}"
    else
        echo -e "${RED}❌ Grafana: Unhealthy${NC}"
    fi
    
    # VictoriaMetrics
    if curl -s http://localhost:8428/health > /dev/null; then
        echo -e "${GREEN}✅ VictoriaMetrics: Healthy${NC}"
    else
        echo -e "${RED}❌ VictoriaMetrics: Unhealthy${NC}"
    fi
    
    # AlertManager
    if curl -s http://localhost:9093/-/healthy > /dev/null; then
        echo -e "${GREEN}✅ AlertManager: Healthy${NC}"
    else
        echo -e "${RED}❌ AlertManager: Unhealthy${NC}"
    fi
}

# Função para mostrar informações de acesso
show_access_info() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    Access Information                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${GREEN}🌐 Web Interfaces:${NC}"
    echo -e "  • Prometheus: ${BLUE}http://localhost:9090${NC}"
    echo -e "  • Grafana: ${BLUE}http://localhost:3000${NC} (admin/admin123)"
    echo -e "  • AlertManager: ${BLUE}http://localhost:9093${NC}"
    echo -e "  • VictoriaMetrics: ${BLUE}http://localhost:8428${NC}"
    echo -e "  • Node Exporter: ${BLUE}http://localhost:9100/metrics${NC}"
    
    echo -e "\n${GREEN}📊 Data Sources:${NC}"
    echo -e "  • Local Prometheus: 15s retention, 30 days"
    echo -e "  • VictoriaMetrics: 30s retention, 90 days"
    echo -e "  • Remote Prometheus: 177.93.132.48:9090"
    
    echo -e "\n${GREEN}🔧 Management Commands:${NC}"
    echo -e "  • View logs: ${YELLOW}docker-compose logs -f [service]${NC}"
    echo -e "  • Stop all: ${YELLOW}docker-compose down${NC}"
    echo -e "  • Restart: ${YELLOW}docker-compose restart [service]${NC}"
    echo -e "  • Status: ${YELLOW}docker-compose ps${NC}"
}

# Função para configurar remote scraping
setup_remote_scraping() {
    echo -e "${YELLOW}🌍 Setting up remote scraping...${NC}"
    
    # Testa conexão com servidor remoto
    if curl -s --connect-timeout 5 http://177.93.132.48:9090/-/healthy > /dev/null; then
        echo -e "${GREEN}✅ Remote Prometheus accessible${NC}"
        
        # Recarrega configuração do Prometheus
        curl -X POST http://localhost:9090/-/reload > /dev/null 2>&1 || true
        
        echo -e "${GREEN}✅ Remote scraping configured${NC}"
    else
        echo -e "${YELLOW}⚠️ Remote Prometheus not accessible, using local only${NC}"
    fi
}

# Função principal
main() {
    print_banner
    
    case "${1:-start}" in
        "start")
            check_dependencies
            create_directories
            setup_permissions
            start_services
            setup_remote_scraping
            check_health
            show_access_info
            ;;
        "stop")
            echo -e "${YELLOW}🛑 Stopping all services...${NC}"
            docker compose down
            echo -e "${GREEN}✅ All services stopped${NC}"
            ;;
        "restart")
            echo -e "${YELLOW}🔄 Restarting all services...${NC}"
            docker compose restart
            check_health
            ;;
        "status")
            docker compose ps
            check_health
            ;;
        "logs")
            docker compose logs -f "${2:-}"
            ;;
        "clean")
            echo -e "${YELLOW}🧹 Cleaning up...${NC}"
            docker compose down -v
            docker system prune -f
            echo -e "${GREEN}✅ Cleanup completed${NC}"
            ;;
        "backup")
            echo -e "${YELLOW}💾 Creating backup...${NC}"
            timestamp=$(date +%Y%m%d_%H%M%S)
            tar -czf "backups/monitoring_stack_${timestamp}.tar.gz" data/
            echo -e "${GREEN}✅ Backup created: backups/monitoring_stack_${timestamp}.tar.gz${NC}"
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  start     - Start all services (default)"
            echo "  stop      - Stop all services"
            echo "  restart   - Restart all services"
            echo "  status    - Show service status"
            echo "  logs      - Show logs (optional: service name)"
            echo "  clean     - Stop and remove all data"
            echo "  backup    - Create backup of data"
            echo "  help      - Show this help"
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $1${NC}"
            echo "Use '$0 help' for available commands"
            exit 1
            ;;
    esac
}

# Executa função principal
main "$@"