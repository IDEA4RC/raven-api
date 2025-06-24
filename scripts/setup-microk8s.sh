#!/bin/bash

# Script para configurar MicroK8s para el despliegue de RAVEN API
# Este script debe ejecutarse ANTES de deploy-all.sh

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🔧 Configuración MicroK8s para RAVEN API${NC}"
echo -e "${CYAN}=======================================${NC}"
echo ""

# Función para mostrar progreso
show_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

# Función para mostrar éxito
show_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Función para mostrar advertencia
show_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Función para mostrar error
show_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar si MicroK8s está instalado
check_microk8s() {
    show_step "Verificando MicroK8s..."
    
    if ! command -v microk8s &> /dev/null; then
        show_error "MicroK8s no está instalado"
        echo "Instalar con: sudo snap install microk8s --classic"
        exit 1
    fi
    
    if ! microk8s status --wait-ready &> /dev/null; then
        show_error "MicroK8s no está corriendo"
        echo "Iniciar con: microk8s start"
        exit 1
    fi
    
    show_success "MicroK8s está corriendo"
}

# Habilitar addons necesarios
enable_addons() {
    show_step "Habilitando addons necesarios..."
    
    # Addons básicos
    microk8s enable dns
    microk8s enable storage
    microk8s enable registry
    
    # Istio (para ingress y service mesh)
    microk8s enable istio
    
    # Cert-manager (para certificados SSL)
    microk8s enable cert-manager
    
    # Prometheus (opcional, también lo desplegamos manualmente)
    microk8s enable prometheus
    
    show_success "Addons habilitados"
}

# Configurar kubectl
setup_kubectl() {
    show_step "Configurando kubectl..."
    
    # Crear alias si no existe
    if ! command -v kubectl &> /dev/null; then
        echo "alias kubectl='microk8s kubectl'" >> ~/.bashrc
        echo "Agregado alias kubectl a ~/.bashrc"
        echo "Ejecuta: source ~/.bashrc"
    fi
    
    # Crear kubeconfig
    mkdir -p ~/.kube
    microk8s config > ~/.kube/config
    
    show_success "kubectl configurado"
}

# Verificar conectividad
verify_setup() {
    show_step "Verificando configuración..."
    
    # Usar microk8s kubectl directamente
    echo "Nodos del cluster:"
    microk8s kubectl get nodes
    echo ""
    
    echo "Namespaces:"
    microk8s kubectl get namespaces
    echo ""
    
    echo "Pods del sistema:"
    microk8s kubectl get pods -n kube-system
    echo ""
    
    echo "Servicios de Istio:"
    microk8s kubectl get svc -n istio-system
    echo ""
    
    show_success "Verificación completada"
}

# Mostrar información de configuración
show_info() {
    echo ""
    echo -e "${CYAN}📋 Información de configuración${NC}"
    echo -e "${CYAN}================================${NC}"
    echo ""
    echo -e "${GREEN}🔧 Comandos útiles MicroK8s:${NC}"
    echo -e "   Ver status:           microk8s status"
    echo -e "   Usar kubectl:         microk8s kubectl <comando>"
    echo -e "   Ver logs:             microk8s kubectl logs <pod>"
    echo -e "   Acceder registry:     microk8s ctr images ls"
    echo ""
    echo -e "${GREEN}🌐 Acceso a servicios:${NC}"
    echo -e "   Istio Ingress:        microk8s kubectl get svc istio-ingressgateway -n istio-system"
    echo -e "   Dashboard:            microk8s dashboard-proxy"
    echo ""
    echo -e "${YELLOW}📝 Próximos pasos:${NC}"
    echo -e "   1. Ejecutar: source ~/.bashrc (para usar alias kubectl)"
    echo -e "   2. Ejecutar: ./scripts/deploy-all.sh deploy"
    echo -e "   3. Configurar DNS apuntando a la IP del nodo MicroK8s"
    echo ""
    echo -e "${YELLOW}💡 Nota: Los certificados SSL pueden tardar unos minutos en generarse${NC}"
}

# Función principal
main() {
    case "${1:-setup}" in
        "setup")
            check_microk8s
            enable_addons
            setup_kubectl
            sleep 30  # Dar tiempo a que los addons se inicialicen
            verify_setup
            show_info
            ;;
        "status")
            verify_setup
            ;;
        "clean")
            show_step "Limpiando configuración MicroK8s..."
            microk8s disable prometheus
            microk8s disable cert-manager
            microk8s disable istio
            microk8s disable registry
            microk8s disable storage
            microk8s disable dns
            show_success "Addons deshabilitados"
            ;;
        "reset")
            show_step "Reiniciando MicroK8s..."
            microk8s reset --destroy-storage
            show_success "MicroK8s reiniciado"
            ;;
        "help")
            echo "Uso: $0 [setup|status|clean|reset|help]"
            echo ""
            echo "Comandos:"
            echo "  setup  - Configurar MicroK8s (por defecto)"
            echo "  status - Verificar estado"
            echo "  clean  - Deshabilitar addons"
            echo "  reset  - Reiniciar MicroK8s completamente"
            echo "  help   - Mostrar esta ayuda"
            ;;
        *)
            show_error "Comando desconocido: $1"
            echo "Usa '$0 help' para ver los comandos disponibles"
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"
