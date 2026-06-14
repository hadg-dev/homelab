import time
import typer
import subprocess
import sys
import os
from scripts.logger import console
from scripts.bootstrap import run, command_exists
from scripts.state import StateManager

app = typer.Typer()
state = StateManager()

def install_helm():
    print("[bold yellow]Installing Helm...[/bold yellow]")

    if command_exists("helm"):
        print("[green]Helm already installed → skipping[/green]")
        return

    run("brew install helm")

    print("[green]Helm installed[/green]")

def install_k9s():
    print("[bold yellow]Installing k9s...[/bold yellow]")

    if command_exists("k9s"):
        print("[green]k9s already installed → skipping[/green]")
        return
    
    run("echo 'Installing k9s...'")
    run("brew install derailed/k9s/k9s")

    print("[green]k9s installed[/green]")


def install_argocd():
    print("[bold yellow]Installing ArgoCD...[/bold yellow]")

    run("kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -")

    client_secret = os.getenv("ARGOCD_OIDC_CLIENT_SECRET")
    if not client_secret:
        print("[red]Missing ARGOCD_OIDC_CLIENT_SECRET env var[/red]")
        raise SystemExit(1)

    print("[bold yellow]Creating OIDC secret...[/bold yellow]")

    run(f"""
kubectl -n argocd create secret generic oidc-keycloak \
  --from-literal=clientSecret='{client_secret}' \
  --dry-run=client -o yaml | kubectl apply -f -
""")

    run("""
helm repo add argo https://argoproj.github.io/argo-helm || true
helm repo update
""")

    run("""
helm upgrade --install argocd argo/argo-cd \
  --namespace argocd \
  --set server.service.type=ClusterIP \
  --set configs.params.server.insecure=true \
  -f gitops/platform/argocd/values.yaml
""")

    print("[green]ArgoCD installed[/green]")


def install_keycloak():
    print("[bold yellow]Installing Keycloak...[/bold yellow]")

    run("kubectl create namespace keycloak --dry-run=client -o yaml | kubectl apply -f -")

    run("helm repo add bitnami https://charts.bitnami.com/bitnami || true")
    run("helm repo update")

    run("""
helm upgrade --install keycloak bitnami/keycloak \
  --namespace keycloak \
  -f gitops/platform/keycloak/values.yaml
""")

    print("[green]Keycloak installed[/green]")



def install_monitoring():
    print("[bold yellow]Installing Monitoring stack (Prometheus + Grafana)...[/bold yellow]")

    # Namespace
    run(
        "kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -"
    )

    # Helm repo
    run("""
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true
helm repo update
""")

    # Install kube-prometheus-stack with Grafana exposed
    run("""
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set grafana.service.type=ClusterIP \
  --set prometheus.service.type=ClusterIP
""")

    print("[green]Monitoring stack installed[/green]")


def step_platform():
    print("[bold yellow]Deploying platform apps...[/bold yellow]")
    if state.get("platform_ready"):
        print("[green]Platform already ready → skipping[/green]")
        return

    print("[bold yellow]Starting platform tooling setup...[/bold yellow]")

    install_helm()
    install_k9s()
    install_argocd()
    #install_keycloak()
    install_monitoring()
    state.set("platform_ready", True)

    print("[green]Platform deployment complete[/green]")



def uninstall_helm_release(name: str, namespace: str):
    print(f"[bold red]Uninstalling {name} in {namespace}[/bold red]")
    run(f"helm uninstall {name} -n {namespace} || true")


def step_platform_down():
    print("[bold red]Destroying platform components...[/bold red]")

    # Argo CD
    uninstall_helm_release("argocd", "argocd")

    # Monitoring stack
    uninstall_helm_release("monitoring", "monitoring")

    # Keycloak (if you enable it later)
    uninstall_helm_release("keycloak", "keycloak")

    # Optional: remove namespaces (clean slate)
    print("[bold yellow]Removing namespaces...[/bold yellow]")
    run("kubectl delete namespace argocd --ignore-not-found")
    run("kubectl delete namespace monitoring --ignore-not-found")
    run("kubectl delete namespace keycloak --ignore-not-found")

    # Optional: remove OIDC secret leftover
    print("[bold yellow]Cleaning secrets...[/bold yellow]")
    run("kubectl delete secret oidc-keycloak -n argocd --ignore-not-found")

    # Reset state
    state.set("platform_ready", False)

    print("[green]Platform destroyed[/green]")

@app.command()
def up():
    step_platform()

@app.command()
def status():
    print(state.load())

@app.command()
def down():
    step_platform_down()

print(__name__)
print(app.registered_commands)


if __name__ == "__main__":
    app()