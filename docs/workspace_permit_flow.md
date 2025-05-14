# Documentación de los modelos y flujo de trabajo - Workspace, Permit y WorkspaceHistory

## Descripción General

Este documento explica la interacción entre Workspace, Permit y WorkspaceHistory en la plataforma RAVEN API.

## Autenticación con Keycloak

La autenticación de usuarios se realiza mediante Keycloak, un sistema de gestión de identidad y acceso. Los usuarios se autentican contra Keycloak, y nuestra API utiliza los tokens JWT de Keycloak para validar las solicitudes.

### Flujo de Autenticación

1. El usuario envía sus credenciales a nuestra API a través del endpoint `/auth/login`
2. Nuestra API reenvía estas credenciales a Keycloak para su validación
3. Si la validación es exitosa, Keycloak devuelve un token JWT
4. Nuestra API devuelve este token al usuario
5. El usuario incluye este token en todas las solicitudes posteriores
6. Nuestra API verifica el token con Keycloak y determina si el usuario tiene acceso

Los IDs de usuario en nuestra base de datos corresponden a los IDs de Keycloak, lo que garantiza consistencia entre ambos sistemas.

## Modelos de Base de Datos

### Workspace

El Workspace representa un espacio donde los investigadores pueden trabajar con datos médicos para sus análisis.

**Atributos principales:**
- `id`: Identificador único del workspace
- `team_id`: Equipo al que pertenece el workspace
- `data_access`: Estado de acceso a los datos (1=Pendiente, 2=Solicitado, 3=Aprobado, 4=Rechazado)
- `last_modification_date`: Última fecha de modificación

### Permit

El Permit representa un permiso para acceder a los datos dentro de un workspace.

**Atributos principales:**
- `id`: Identificador único del permiso
- `workspace_id`: Workspace al que pertenece este permiso
- `status`: Estado del permiso (1=Pendiente, 2=Solicitado, 3=Aprobado, 4=Rechazado)
- `update_date`: Fecha de última actualización

### WorkspaceHistory

El WorkspaceHistory registra todos los cambios y eventos importantes que ocurren en un workspace.

**Atributos principales:**
- `id`: Identificador único del registro histórico
- `workspace_id`: Workspace al que pertenece este registro
- `creator_id`: Usuario que realizó la acción
- `date`: Fecha del evento
- `action`: Descripción corta de la acción realizada
- `phase`: Fase en la que se encuentra el workspace
- `details`: Detalles adicionales sobre el evento

## Flujo de Trabajo

1. **Creación del Workspace**:
   - Se crea un nuevo Workspace
   - Se crea un Permit inicial con estado "Pendiente"
   - Se registra en WorkspaceHistory la creación del Workspace

2. **Solicitud de Acceso a Datos**:
   - El usuario actualiza el Permit a estado "Solicitado"
   - Se actualiza el Workspace con data_access="Solicitado"
   - Se registra en WorkspaceHistory el evento de solicitud

3. **Aprobación/Rechazo del Permiso**:
   - Un administrador actualiza el Permit a "Aprobado" o "Rechazado"
   - Se actualiza el Workspace correspondiente
   - Se registra en WorkspaceHistory el evento de aprobación/rechazo

## Estados y Constantes

Los estados se definen como enumeraciones en `app/utils/constants.py`:

```python
class PermitStatus(int, Enum):
    PENDING = 1
    SUBMITTED = 2
    APPROVED = 3
    REJECTED = 4

class DataAccessStatus(int, Enum):
    PENDING = 1
    SUBMITTED = 2
    APPROVED = 3
    REJECTED = 4
```

## Endpoints Principales

### Workspaces

- `POST /workspaces/`: Crea un nuevo workspace
- `GET /workspaces/{workspace_id}`: Obtiene un workspace por ID
- `PATCH /workspaces/{workspace_id}/data-access`: Actualiza el estado de acceso a datos

### Permits

- `GET /permits/{permit_id}`: Obtiene un permiso por ID
- `GET /permits/workspace/{workspace_id}`: Obtiene todos los permisos de un workspace
- `PATCH /permits/{permit_id}/status`: Actualiza el estado de un permiso

### Workspace History

- `GET /workspace-history/{workspace_id}`: Obtiene el historial de un workspace

## Integración

El endpoint `/test-integration/submit-permit-request` muestra cómo se integran estos tres componentes:
1. Actualiza el estado del permiso
2. Actualiza el estado del workspace
3. Genera entradas en el historial automáticamente

## Diagrama de Secuencia

```
Usuario -> API: Solicitar acceso a datos
API -> Permit: Actualizar estado a SUBMITTED
Permit -> Workspace: Actualizar data_access a SUBMITTED
API -> WorkspaceHistory: Crear registro de la acción
API -> Usuario: Respuesta con resultado
```
