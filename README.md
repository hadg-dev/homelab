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


## Testing k8sGPT

```bash
kubectl config current-context
kubectl cluster-info
brew tap k8sgpt-ai/k8sgpt
brew install k8sgpt
k8sgpt auth add -b google -p "$GEMINI_API_KEY" -m "gemini-3.5-flash"
k8sgpt auth default --provider google 
k8sgpt auth list
```

```bash
kubectl apply -f broken-pod.yaml 
# local analyse only, use always as first run do not consume any token
k8sgpt analyze

# using the LLM connected (here Gemini)
k8sgpt analyse --explain
k8sgpt analyze --explain --namespace argocd
k8sgpt analyze --explain --filter Ingress
k8sgpt analyze --explain --filter Ingress --namespace monitoring
```

To restrict our analysis we may filter components scanned by default
```bash
k8sgpt filters list
```

```bash
k8sgpt integrations list
Active:
Unused: 
> prometheus
> aws
> keda
> kyverno
```

Yes, you can absolutely set up monitoring and alerts, but you must use the k8sgpt Operator to do this, as the CLI tool is designed for "one-off" manual checks.

How it works:
Continuous Scanning: When installed as an operator (using Helm), k8sgpt runs as a controller inside your cluster. It performs periodic scans of your resources.

Prometheus Integration: The operator exposes Prometheus-compatible metrics. By enabling the ServiceMonitor in the Helm chart, your Prometheus instance can scrape these diagnostic results.

Alerting Rules: Once your metrics are in Prometheus, you can create standard Prometheus Alerting Rules (Alertmanager) based on k8sgpt findings. For example, you could alert if the number of "unhealthy" resources reported by k8sgpt exceeds a certain threshold.

External Notifications: The operator can be configured to forward diagnostic results to external sinks like Slack, email, or your CI/CD pipelines, providing you with human-readable summaries whenever an issue is detected.


### uninstall the CLI version
brew uninstall k8sgpt
brew untap k8sgpt-ai/k8sgpt
rm -rf ~/Library/Application\ Support/k8sgpt

### installing the k8sGPT operator

```bash
helm install k8sgpt k8sgpt/k8sgpt-operator -n k8sgpt-operator-system \
  --create-namespace \
  --set serviceMonitor.enabled=true \
  --set grafanaDashboard.enabled=true
```


# How to use homelab

## Upload files from host (macOS) into multipass (VMs)

| 🎨 Type | 🎯 Action | 💻 Command | 💡 DevOps Pro Tip |
| :--- | :--- | :--- | :--- |
| 📤 **Copy** | Host ➡️ VM | `multipass transfer ./local.yml node1:/tmp/` | Faster than mounts for single, static artifacts (like raw manifests). |
| 📥 **Copy** | VM ➡️ Host | `multipass transfer node1:/var/log/syslog ./` | Great for extracting logs or generated kubeconfigs locally. |
| 🔗 **Mount** | Map Host to VM | `multipass mount ~/dev/repo node1:/workspace` | Native mounts. UID/GID mappings are handled automatically by `multipassd`. |
| ✂️ **Unmount**| Remove mapping | `multipass unmount node1` | Run this before tearing down/rebuilding to avoid stale file handles. |
| 🔍 **Inspect**| Check mounts | `multipass info node1` | Will list all currently active mounts under the `Mounts:` section. |
| 🚀 **Exec** | Read directly | `multipass exec node1 -- cat /etc/hosts > hosts.txt` | Alternative to `transfer` if you just need to dump stdout to a local file. |