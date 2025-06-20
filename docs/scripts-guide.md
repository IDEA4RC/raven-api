# RAVEN API Scripts - Documentation

This document describes all available scripts in the RAVEN API project and their functionality.

## 📁 Main Scripts

### 🚀 **Deployment and Configuration**

#### `quick-start.sh`
**Purpose**: Quick development environment setup
**Usage**: `./scripts/quick-start.sh`
**Description**: 
- Installs dependencies with uv/pip
- Sets up PostgreSQL with Docker
- Runs database migrations
- Optionally seeds the database

#### `setup-postgresql.sh`
**Purpose**: Set up PostgreSQL using standalone Docker
**Usage**: `./scripts/setup-postgresql.sh`
**Description**:
- Creates and runs PostgreSQL container
- Configures `raven_db` database
- User: `raven_user`, password: `raven_password`

#### `setup-postgresql-compose.sh`
**Purpose**: Set up PostgreSQL using Docker Compose
**Usage**: `./scripts/setup-postgresql-compose.sh`
**Description**:
- Uses docker-compose.postgres.yml
- More robust configuration for development
- Includes persistent volumes

### 🐳 **Docker and Kubernetes**

#### `build-docker.sh`
**Purpose**: Build and push Docker images
**Usage**: 
```bash
./scripts/build-docker.sh [version]
./scripts/build-docker.sh v1.0.0
```
**Description**:
- Builds Docker image for the API
- Supports multiple registries
- Automatic tagging

#### `deploy-k8s.sh`
**Purpose**: Complete Kubernetes deployment
**Usage**: `./scripts/deploy-k8s.sh`
**Description**:
- Deploys PostgreSQL and API to Kubernetes
- Creates `raven-api` namespace
- Configures health checks
- Supports Istio automatically

#### `verify-k8s.sh`
**Purpose**: Verify Kubernetes cluster readiness
**Usage**: `./scripts/verify-k8s.sh`
**Description**:
- Verifies cluster connectivity
- Reviews storage classes
- Detects Istio and LoadBalancer
- Shows available resources

### 🗄️ **Database**

#### `migrate_to_postgresql.sh`
**Purpose**: Complete migration from SQLite to PostgreSQL
**Usage**: `./scripts/migrate_to_postgresql.sh`
**Description**:
- Automatically sets up PostgreSQL
- Migrates existing data from SQLite
- Creates tables with SQLAlchemy
- Fully automated process

#### `migrate_data.py`
**Purpose**: Migrate data from SQLite to PostgreSQL (internal script)
**Usage**: `python scripts/migrate_data.py`
**Description**:
- Transfers data preserving integrity
- Automatically converts data types
- Respects foreign keys

#### `create_tables.py`
**Purpose**: Create table structure in PostgreSQL
**Usage**: `python scripts/create_tables.py`
**Description**:
- Creates tables using SQLAlchemy models
- Idempotent (doesn't fail if they already exist)
- Alternative to Alembic migrations

#### `seed_db.py`
**Purpose**: Populate database with test data
**Usage**: `python scripts/seed_db.py`
**Description**:
- Creates example users, workspaces, and permits
- Realistic data for testing
- Safe to execute multiple times

## 🎛️ **Legacy Scripts**

### `raven-ctl.sh`
**Purpose**: Comprehensive control script for MicroK8s/Istio (legacy)
**Usage**: `./raven-ctl.sh [command]`
**Available commands**:
- `deploy` - Deploy application
- `expose` - Expose to internet
- `secure` - Configure HTTPS
- `verify` - Verify accessibility
- `status` - View status
- `restart` - Restart deployment
- `cleanup` - Clean up resources

**Note**: This script is intended for specific configurations with MicroK8s and Istio. For new deployments, it's recommended to use the modern Kubernetes scripts.

## 🔄 **Recommended Workflows**

### Local Development
```bash
# 1. Initial setup
./scripts/quick-start.sh

# 2. Start API
uvicorn main:app --reload
```

### SQLite to PostgreSQL Migration
```bash
# Complete automatic migration
./scripts/migrate_to_postgresql.sh
```

### Kubernetes Deployment
```bash
# 1. Verify cluster
./scripts/verify-k8s.sh

# 2. Build image
./scripts/build-docker.sh

# 3. Deploy
./scripts/deploy-k8s.sh
```

### Manual PostgreSQL Setup
```bash
# Option 1: Simple Docker
./scripts/setup-postgresql.sh

# Option 2: Docker Compose
./scripts/setup-postgresql-compose.sh

# Create tables
python scripts/create_tables.py

# Populate with test data
python scripts/seed_db.py
```

## 🗑️ **Removed Scripts**

The following scripts were removed for being obsolete:

### From root directory:
- `deploy-complete.sh` - Replaced by `deploy-k8s.sh`
- `expose-securely.sh` - Functionality integrated into `raven-ctl.sh`
- `expose-to-internet.sh` - Functionality integrated into `raven-ctl.sh`
- `run.py` - Use `uvicorn` directly

### From scripts/ directory:
- `fix_migrations.py` - No longer needed with PostgreSQL
- `update_permits_table.py` - SQLite-specific
- `update_users_table.py` - SQLite-specific
- `setup-dev.sh` - Replaced by `quick-start.sh`
- `test_api_endpoints.sh` - Functionality in tests/
- `test_api_endpoints_new.sh` - Functionality in tests/
- `test_api_without_auth.py` - Functionality in tests/
- `create_test_user.py` - Functionality in `seed_db.py`
- `check-istio.sh` - Integrated into `raven-ctl.sh`
- `check-registry.sh` - Integrated into `raven-ctl.sh`
- `deploy.sh` - Replaced by `deploy-k8s.sh`
- `generate-tls-cert.sh` - Integrated into `raven-ctl.sh`
- `get-external-ip.sh` - Integrated into `raven-ctl.sh`
- `setup-metallb.sh` - Integrated into `raven-ctl.sh`
- `verify-api-access.sh` - Integrated into `raven-ctl.sh`

## 📋 **Useful Command Summary**

```bash
# Quick development
./scripts/quick-start.sh && uvicorn main:app --reload

# Complete Kubernetes
./scripts/verify-k8s.sh && ./scripts/build-docker.sh && ./scripts/deploy-k8s.sh

# PostgreSQL only
./scripts/setup-postgresql-compose.sh && python scripts/create_tables.py

# Migration from SQLite
./scripts/migrate_to_postgresql.sh
```

---

**Note**: All scripts include help/documentation. Run any script without parameters or with `--help` to get specific information.
