#!/bin/bash
set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

show_progress() {
    echo -e "${BLUE}▶️  $1${NC}"
}

show_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

show_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Configuración
IMAGE_NAME="raven-api"
VERSION=${1:-latest}
REGISTRY=${DOCKER_REGISTRY:-localhost:32000}
FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME:$VERSION"

echo "🐳 Construyendo imagen Docker para RAVEN API..."
echo "   - Imagen: $FULL_IMAGE_NAME"
echo

# Verificar que Docker está disponible
if ! command -v docker &> /dev/null; then
    show_error "Docker no está instalado o no está en el PATH"
    exit 1
fi

# Construir la imagen
show_progress "1. Construyendo imagen Docker..."
docker build -t $FULL_IMAGE_NAME .

if [ $? -eq 0 ]; then
    show_success "Imagen construida exitosamente"
else
    show_error "Error al construir la imagen"
    exit 1
fi

# Etiquetar también como latest si no es latest
if [ "$VERSION" != "latest" ]; then
    show_progress "2. Etiquetando como latest..."
    docker tag $FULL_IMAGE_NAME $REGISTRY/$IMAGE_NAME:latest
fi

# Intentar subir al registry si está configurado
if [ "$REGISTRY" != "localhost:32000" ]; then
    show_progress "3. Subiendo imagen al registry..."
    docker push $FULL_IMAGE_NAME
    
    if [ "$VERSION" != "latest" ]; then
        docker push $REGISTRY/$IMAGE_NAME:latest
    fi
    
    if [ $? -eq 0 ]; then
        show_success "Imagen subida exitosamente al registry"
    else
        show_error "Error al subir la imagen al registry"
        exit 1
    fi
else
    show_progress "3. Subiendo imagen al registry local de MicroK8s..."
    docker push $FULL_IMAGE_NAME
    
    if [ "$VERSION" != "latest" ]; then
        docker push $REGISTRY/$IMAGE_NAME:latest
    fi
    
    if [ $? -eq 0 ]; then
        show_success "Imagen subida exitosamente al registry local"
    else
        show_error "Error al subir la imagen al registry local"
        # No salir con error para registry local ya que podría no estar disponible
    fi
fi

echo
show_success "🎉 Proceso completado!"
echo "   - Imagen: $FULL_IMAGE_NAME"
echo "   - Tamaño: $(docker images $FULL_IMAGE_NAME --format "table {{.Size}}" | tail -n +2)"
echo
echo "🚀 Para desplegar en Kubernetes:"
echo "   ./scripts/deploy-k8s.sh"
echo
echo "🧪 Para probar localmente:"
echo "   docker run -p 8000:8000 -e DATABASE_URI=postgresql://user:pass@host:5432/db $FULL_IMAGE_NAME"
