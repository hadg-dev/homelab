# Homelab - Automated Kubernetes Cluster

A comprehensive Python/Typer-based automation framework for provisioning and managing a self-hosted Kubernetes homelab on macOS using Multipass and k3s.

## Project Architecture

This project follows a **4-layer bootstrap model** with idempotent state management:

### Layer 0: Cluster Provisioning
**Bootstrap** - `scripts/bootstrap.py`
- Provisions Multipass VMs (control plane + workers)
- Installs and configures k3s lightweight Kubernetes
- Sets up local kubeconfig for cluster access
- Validates cluster health

### Layer 1: Platform Services
**Platform** - `scripts/platform.py`
- Installs Helm package manager
- Deploys ArgoCD for GitOps-based deployment
- Configures OIDC integration with Keycloak
- Sets up monitoring stack (Prometheus + Grafana)

### Layer 2: Ingress & Networking
**Ingress** - `scripts/ingress.py`
- Deploys Traefik ingress controller (k3s default)
- Configures service exposure for ArgoCD, Grafana, Prometheus
- Manages local DNS entries via `/etc/hosts`

### Layer 3: Security & TLS
**TLS** - `scripts/tls.py`
- Installs cert-manager
- Creates self-signed root CA
- Issues certificates for all local services (argocd.local, grafana.local, prometheus.local)
- Exports CA certificate for client installation

## Certificate Chain

```
homelab-selfsigned (root issuer)
        │
        ▼
homelab-root-ca (internal CA)
        │
        ├── grafana.local
        ├── argocd.local
        └── prometheus.local
```

## Quick Start

### Prerequisites
- macOS with Homebrew
- Multipass 10.15+
- 6+ GB RAM available (for VMs)

### Installation
```bash
# 1. Bootstrap cluster (VMs + k3s)
make bootstrap

# 2. Deploy platform services
make platform-up

# 3. Setup ingress & networking
make ingress
make hosts

# 4. Configure TLS
make tls
make export-ca
```

## Available Commands

```bash
# Cluster management
make bootstrap      # Provision VMs and k3s cluster
make status         # Check cluster status
make downstrap      # Stop cluster

# Platform services
make platform-up    # Install ArgoCD, Monitoring, Keycloak
make platform-down  # Remove platform services

# Networking
make ingress        # Deploy ingress controller
make hosts          # Display /etc/hosts entries needed

# TLS/Security
make tls            # Install cert-manager and certificates
make reset-tls      # Remove TLS configuration
make export-ca      # Export root CA certificate

# Utilities
make k8sgpt-install # Install k8sgpt for cluster diagnostics
make destroy        # Full environment teardown
```

## Accessing Services

Once configured, services are accessible locally:

```bash
# Prometheus (metrics)
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090
open http://prometheus.local:9090

# Grafana (dashboards)
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
open http://grafana.local:3000

# ArgoCD (GitOps)
open https://argocd.local
```

## Multipass VM Networking

To enable bridged networking on your local network:

```bash
# Configure bridge interface (e.g., en0)
multipass set local.bridged-network=en0

# Enable bridging for each VM
multipass set local.k8s-ctrl.bridged=true
multipass set local.k8s-worker-1.bridged=true
multipass set local.k8s-worker-2.bridged=true
```

## State Management

The project uses `state.json` to track bootstrap progress, enabling safe re-runs of setup steps. State tracks:
- Cluster readiness
- Platform installation status
- TLS configuration completion

## Technology Stack

- **Infrastructure**: Multipass + k3s
- **Orchestration**: Kubernetes 1.x
- **GitOps**: ArgoCD
- **Authentication**: Keycloak (OIDC)
- **Monitoring**: Prometheus + Grafana + kube-prometheus-stack
- **Ingress**: Traefik
- **Certificates**: cert-manager
- **CLI**: Python 3.13+ with Typer + Rich
- **Package Manager**: uv


