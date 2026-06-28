import os

import typer

from scripts.bootstrap import command_exists, run
from scripts.logger import console
from scripts.state import StateManager

app = typer.Typer()
state = StateManager()


def install_helm() -> None:
    console.print("[bold yellow]Installing Helm...[/bold yellow]")

    if command_exists("helm"):
        console.print("[green]Helm already installed → skipping[/green]")
        return

    run("brew install helm")

    console.print("[green]Helm installed[/green]")


def install_k9s() -> None:
    console.print("[bold yellow]Installing k9s...[/bold yellow]")

    if command_exists("k9s"):
        console.print("[green]k9s already installed → skipping[/green]")
        return

    run("echo 'Installing k9s...'")
    run("brew install derailed/k9s/k9s")

    console.print("[green]k9s installed[/green]")


def install_argocd() -> None:
    console.print("[bold yellow]Installing ArgoCD...[/bold yellow]")

    run("kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -")

    client_secret = os.getenv("ARGOCD_OIDC_CLIENT_SECRET")
    if not client_secret:
        console.print("[red]Missing ARGOCD_OIDC_CLIENT_SECRET env var[/red]")
        raise SystemExit(1)

    console.print("[bold yellow]Creating OIDC secret...[/bold yellow]")

    run(
        f"kubectl -n argocd create secret generic oidc-keycloak \\\n"
        f"  --from-literal=clientSecret='{client_secret}' \\\n"
        f"  --dry-run=client -o yaml | kubectl apply -f -"
    )

    run(
        "helm repo add argo https://argoproj.github.io/argo-helm || true\n"
        "helm repo update"
    )

    run(
        "helm upgrade --install argocd argo/argo-cd \\\n"
        "  --namespace argocd \\\n"
        "  --set server.service.type=ClusterIP \\\n"
        "  --set configs.params.server.insecure=true \\\n"
        "  -f gitops/platform/argocd/values.yaml"
    )

    console.print("[green]ArgoCD installed[/green]")


def install_keycloak() -> None:
    console.print("[bold yellow]Installing Keycloak...[/bold yellow]")

    run("kubectl create namespace keycloak --dry-run=client -o yaml | kubectl apply -f -")

    run("helm repo add bitnami https://charts.bitnami.com/bitnami || true")
    run("helm repo update")

    run(
        "helm upgrade --install keycloak bitnami/keycloak \\\n"
        "  --namespace keycloak \\\n"
        "  -f gitops/platform/keycloak/values.yaml"
    )

    console.print("[green]Keycloak installed[/green]")


def install_monitoring() -> None:
    console.print(
        "[bold yellow]Installing Monitoring stack "
        "(Prometheus + Grafana)...[/bold yellow]"
    )

    # Namespace
    run(
        "kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -"
    )

    # Helm repo
    run(
        "helm repo add prometheus-community "
        "https://prometheus-community.github.io/helm-charts || true\n"
        "helm repo update"
    )

    # Install kube-prometheus-stack with Grafana exposed
    run(
        "helm upgrade --install monitoring "
        "prometheus-community/kube-prometheus-stack \\\n"
        "  --namespace monitoring \\\n"
        "  --set grafana.service.type=ClusterIP \\\n"
        "  --set prometheus.service.type=ClusterIP"
    )

    console.print("[green]Monitoring stack installed[/green]")


def step_platform() -> None:
    console.print("[bold yellow]Deploying platform apps...[/bold yellow]")
    if state.get("platform_ready"):
        console.print("[green]Platform already ready → skipping[/green]")
        return

    console.print("[bold yellow]Starting platform tooling setup...[/bold yellow]")

    install_helm()
    install_k9s()
    install_argocd()
    # install_keycloak()
    install_monitoring()
    state.set("platform_ready", True)

    console.print("[green]Platform deployment complete[/green]")


def uninstall_helm_release(name: str, namespace: str) -> None:
    console.print(f"[bold red]Uninstalling {name} in {namespace}[/bold red]")
    run(f"helm uninstall {name} -n {namespace} || true")


def step_platform_down() -> None:
    console.print("[bold red]Destroying platform components...[/bold red]")

    # Argo CD
    uninstall_helm_release("argocd", "argocd")

    # Monitoring stack
    uninstall_helm_release("monitoring", "monitoring")

    # Keycloak (if you enable it later)
    uninstall_helm_release("keycloak", "keycloak")

    # Optional: remove namespaces (clean slate)
    console.print("[bold yellow]Removing namespaces...[/bold yellow]")
    run("kubectl delete namespace argocd --ignore-not-found")
    run("kubectl delete namespace monitoring --ignore-not-found")
    run("kubectl delete namespace keycloak --ignore-not-found")

    # Optional: remove OIDC secret leftover
    console.print("[bold yellow]Cleaning secrets...[/bold yellow]")
    run("kubectl delete secret oidc-keycloak -n argocd --ignore-not-found")

    # Reset state
    state.set("platform_ready", False)

    console.print("[green]Platform destroyed[/green]")


@app.command()
def up() -> None:
    step_platform()


@app.command()
def status() -> None:
    console.print(state.load())


@app.command()
def down() -> None:
    step_platform_down()


if __name__ == "__main__":
    app()