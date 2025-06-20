# Despliegue en Kubernetes - RAVEN API

Esta guía detalla cómo desplegar la API de RAVEN en un cluster de Kubernetes con PostgreSQL.

## 📋 Prerrequisitos

- **Kubernetes cluster** funcionando (minikube, microk8s, GKE, EKS, AKS, etc.)
- **kubectl** configurado para conectar al cluster
- **Docker** para construir imágenes
- **Istio** (opcional) para configuración avanzada de networking

## 🚀 Despliegue Rápido

### 1. Construir y Subir la Imagen Docker

```bash
# Construir imagen para registry local (microk8s)
./scripts/build-docker.sh

# O con versión específica
./scripts/build-docker.sh v1.0.0
```

### 2. Desplegar en Kubernetes

```bash
# Despliegue completo automático
./scripts/deploy-k8s.sh
```

Este script:
- ✅ Crea el namespace `raven-api`
- ✅ Aplica secrets y configuraciones
- ✅ Despliega PostgreSQL con almacenamiento persistente
- ✅ Inicializa la base de datos
- ✅ Despliega la API con health checks
- ✅ Configura servicios y networking
- ✅ Aplica configuración de Istio (si está disponible)

## 🔧 Despliegue Manual

Si prefieres control manual sobre el proceso:

```bash
# 1. Crear namespace
kubectl create namespace raven-api

# 2. Aplicar configuraciones base
kubectl apply -n raven-api -f kubernetes/secrets.yaml
kubectl apply -n raven-api -f kubernetes/configmap.yaml

# 3. Desplegar PostgreSQL
kubectl apply -n raven-api -f kubernetes/postgres-deployment.yaml

# 4. Esperar a que PostgreSQL esté listo
kubectl wait --for=condition=ready pod -l app=postgres -n raven-api --timeout=120s

# 5. Inicializar base de datos
kubectl apply -n raven-api -f kubernetes/configmap.yaml

# 6. Desplegar API
kubectl apply -n raven-api -f kubernetes/deployment.yaml
kubectl apply -n raven-api -f kubernetes/service.yaml

# 7. (Opcional) Configurar Istio
kubectl apply -n raven-api -f kubernetes/gateway.yaml
kubectl apply -n raven-api -f kubernetes/virtual-service.yaml
```

## 🌍 Configuración para Diferentes Entornos

### Desarrollo Local
```bash
kubectl apply -k kubernetes/
```

### Producción
```bash
# Editar archivos en kubernetes/overlays/production/
kubectl apply -k kubernetes/overlays/production/
```

## 📊 Verificación del Despliegue

### Ver estado de los pods
```bash
kubectl get pods -n raven-api -w
```

### Ver logs de la API
```bash
kubectl logs -f deployment/raven-api -n raven-api
```

### Ver logs de PostgreSQL
```bash
kubectl logs -f deployment/postgres -n raven-api
```

### Verificar salud de la API
```bash
# Port-forward para acceso local
kubectl port-forward service/raven-api-service 8000:8000 -n raven-api

# Probar endpoint
curl http://localhost:8000/raven-api/v1/health/
```

## 🔒 Configuración de Seguridad

### Actualizar Secrets
```bash
# Editar secrets
kubectl edit secret raven-api-secrets -n raven-api

# O aplicar nuevo archivo
kubectl apply -f kubernetes/secrets.yaml -n raven-api
```

### Variables importantes a configurar:
- `database-uri`: URL completa de PostgreSQL
- `secret-key`: Clave secreta para JWT (usar generador seguro)
- `postgres-password`: Contraseña segura para PostgreSQL

## 🚦 Monitoreo y Observabilidad

### Health Checks
La API incluye health checks automáticos:
- **Readiness Probe**: `/raven-api/v1/health/`
- **Liveness Probe**: `/raven-api/v1/health/`

### Métricas (con Istio)
```bash
# Acceder a Grafana
kubectl port-forward service/grafana 3000:3000 -n istio-system

# Acceder a Kiali
kubectl port-forward service/kiali 20001:20001 -n istio-system
```

## 📈 Escalado

### Escalar API
```bash
kubectl scale deployment raven-api --replicas=3 -n raven-api
```

### Escalado automático (HPA)
```bash
kubectl autoscale deployment raven-api --cpu-percent=70 --min=2 --max=10 -n raven-api
```

## 🗄️ Gestión de Base de Datos

### Backup de PostgreSQL
```bash
kubectl exec -it deployment/postgres -n raven-api -- pg_dump -U raven_user raven_db > backup.sql
```

### Restaurar backup
```bash
kubectl exec -i deployment/postgres -n raven-api -- psql -U raven_user -d raven_db < backup.sql
```

### Acceso directo a PostgreSQL
```bash
kubectl exec -it deployment/postgres -n raven-api -- psql -U raven_user -d raven_db
```

## 🔄 Actualizaciones

### Rolling Update
```bash
# Actualizar imagen
kubectl set image deployment/raven-api raven-api=localhost:32000/raven-api:v1.1.0 -n raven-api

# Ver progreso
kubectl rollout status deployment/raven-api -n raven-api
```

### Rollback
```bash
kubectl rollout undo deployment/raven-api -n raven-api
```

## 🛠️ Troubleshooting

### Problemas comunes

#### API no arranca
```bash
# Ver logs detallados
kubectl logs deployment/raven-api -n raven-api --previous

# Verificar configuración
kubectl describe deployment raven-api -n raven-api
```

#### PostgreSQL no conecta
```bash
# Verificar service
kubectl get svc postgres-service -n raven-api

# Probar conectividad
kubectl run -it --rm debug --image=postgres:15 --restart=Never -n raven-api -- psql -h postgres-service -U raven_user -d raven_db
```

#### Problemas de almacenamiento
```bash
# Verificar PVC
kubectl get pvc -n raven-api

# Ver eventos
kubectl get events -n raven-api --sort-by=.metadata.creationTimestamp
```

## 🌐 Configuración de Red

### Exposición externa (LoadBalancer)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: raven-api-external
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: raven-api
```

### Exposición externa (Ingress)
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: raven-api-ingress
spec:
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: raven-api-service
            port:
              number: 8000
```

## 📚 Referencias

- [Documentación de Kubernetes](https://kubernetes.io/docs/)
- [Configuración de PostgreSQL en K8s](https://kubernetes.io/docs/tutorials/stateful-application/postgresql/)
- [Istio Service Mesh](https://istio.io/latest/docs/)
- [Kustomize](https://kustomize.io/)

---

**¿Necesitas ayuda?** Revisa los logs y eventos de Kubernetes, o consulta la documentación específica de tu proveedor de cluster.
