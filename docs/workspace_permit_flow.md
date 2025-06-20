# Models and Workflow Documentation - Workspace, Permit and WorkspaceHistory

## Overview

This document explains the interaction between Workspace, Permit and WorkspaceHistory in the RAVEN API platform.

## Keycloak Authentication

User authentication is handled through Keycloak, an identity and access management system. Users authenticate against Keycloak, and our API uses Keycloak JWT tokens to validate requests.

### Authentication Flow

1. User sends credentials to our API through the `/raven-api/v1/auth/login` endpoint
2. Our API forwards these credentials to Keycloak for validation
3. If validation is successful, Keycloak returns a JWT token
4. Our API returns this token to the user
5. User includes this token in all subsequent requests
6. Our API verifies the token with Keycloak and determines if the user has access

User IDs in our database correspond to Keycloak IDs, ensuring consistency between both systems.

## Database Models

### Workspace

The Workspace represents a space where researchers can work with medical data for their analyses.

**Main attributes:**
- `id`: Unique workspace identifier
- `team_ids`: Teams that the workspace belongs to (array of strings)
- `data_access`: Data access status (1=Pending, 2=Requested, 3=Approved, 4=Rejected)
- `last_modification_date`: Last modification date

### Permit

The Permit represents permission to access data within a workspace.

**Main attributes:**
- `id`: Unique permit identifier
- `workspace_id`: Workspace this permit belongs to
- `status`: Permit status (1=Pending, 2=Requested, 3=Approved, 4=Rejected)
- `update_date`: Last update date

### WorkspaceHistory

The WorkspaceHistory records all important changes and events that occur in a workspace.

**Main attributes:**
- `id`: Unique historical record identifier
- `workspace_id`: Workspace this record belongs to
- `creator_id`: User who performed the action
- `date`: Event date
- `action`: Short description of the action performed
- `phase`: Phase the workspace is in
- `details`: Additional details about the event

## Workflow

1. **Workspace Creation**:
   - A new Workspace is created
   - An initial Permit is created with "Pending" status
   - The Workspace creation is recorded in WorkspaceHistory

2. **Data Access Request**:
   - User updates the Permit to "Requested" status
   - The Workspace is updated with data_access="Requested"
   - The request event is recorded in WorkspaceHistory

3. **Permit Approval/Rejection**:
   - An administrator updates the Permit to "Approved" or "Rejected"
   - The corresponding Workspace is updated
   - The approval/rejection event is recorded in WorkspaceHistory

## States and Constants

States are defined as enumerations in `app/utils/constants.py`:

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

## Main Endpoints

### Workspaces

- `POST /workspaces/`: Creates a new workspace
- `GET /workspaces/{workspace_id}`: Gets a workspace by ID
- `PATCH /workspaces/{workspace_id}/data-access`: Updates data access status
- `GET /workspaces/`: Lists workspaces (with optional user_id filter)
- `DELETE /workspaces/{workspace_id}`: Deletes a workspace

### Permits

- `GET /permits/{permit_id}`: Gets a permit by ID
- `GET /permits/workspace/{workspace_id}`: Gets all permits for a workspace
- `PATCH /permits/{permit_id}/status`: Updates permit status
- `POST /permits/`: Creates a new permit
- `PUT /permits/{permit_id}`: Updates a permit
- `DELETE /permits/{permit_id}`: Deletes a permit

### Workspace History

- `GET /workspace-history/{workspace_id}`: Gets workspace history

### Authentication

- `POST /auth/login`: Authenticates user with Keycloak
- `GET /auth/me`: Gets current user information

## Integration

The API endpoints show how these three components integrate:
1. Update permit status
2. Update workspace status
3. Automatically generate history entries

## Sequence Diagram

```
User -> API: Request data access
API -> Permit: Update status to SUBMITTED
Permit -> Workspace: Update data_access to SUBMITTED
API -> WorkspaceHistory: Create action record
API -> User: Response with result
```
