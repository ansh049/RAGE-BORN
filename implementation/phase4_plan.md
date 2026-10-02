# Phase 4 Implementation Plan: Plugin Ecosystem & Docker Integration

## Goal Description
Expand RAGE to support third-party, dynamically loaded plugins, and give it native, deep integration with Docker and Kubernetes for DevOps automation.

## Proposed Changes

### 1. Plugin Architecture
- **Location**: `~/.rage/plugins/`
- **Mechanism**: Update `rage/tools/registry.py` to automatically scan `~/.rage/plugins/` for Python files that export subclasses of `BaseTool`.
- **Sandboxing**: (Future consideration) Plugins currently run with the same permissions as RAGE.

### 2. Docker Tool Module (`rage/tools/docker.py`)
- **`docker_run`**: Spawn containers.
- **`docker_ps`**: List active containers.
- **`docker_logs`**: Stream or fetch logs from a specific container.
- **`docker_exec`**: Run commands inside a running container.

### 3. Kubernetes Tool Module (`rage/tools/k8s.py`)
- **`kubectl_get`**: Fetch resources (pods, services, deployments).
- **`kubectl_logs`**: Retrieve logs from a pod.
- **`kubectl_apply`**: Apply a yaml manifest file.

### 4. VS Code Bridge (Optional)
- Setup a lightweight WebSocket server in RAGE that a VS Code extension can connect to, allowing RAGE to read the active editor tab.

## Verification Plan
### Automated Tests
- Test dynamic loading by dropping a dummy tool into `~/.rage/plugins/`.
- Verify `docker_ps` executes successfully (requires Docker daemon).

### Manual Verification
- Ask RAGE to "spin up an nginx container on port 8080".
- Verify RAGE can fetch logs and stop the container.
