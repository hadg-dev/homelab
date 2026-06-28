from pathlib import Path

import typer

from scripts.bootstrap import run
from scripts.logger import console

app = typer.Typer()


def install_cert_manager() -> None:
    run(
        "helm repo add jetstack https://charts.jetstack.io || true\n"
        "helm repo update"
    )

    run(
        "helm upgrade --install cert-manager jetstack/cert-manager \\\n"
        "  --namespace cert-manager \\\n"
        "  --create-namespace \\\n"
        "  --set crds.enabled=true"
    )


def install_tls() -> None:
    console.print("[bold yellow]Applying TLS manifests...[/bold yellow]")

    install_cert_manager()
    run(
        "kubectl wait \\\n"
        "    --for=condition=Available \\\n"
        "    deployment/cert-manager \\\n"
        "    -n cert-manager \\\n"
        "    --timeout=300s"
    )
    run("kubectl apply -f k8s/security/")

    console.print("[green]TLS configured[/green]")


def export_ca() -> None:
    Path("certs").mkdir(exist_ok=True)

    run(
        "kubectl get secret homelab-root-ca-secret \\\n"
        "      -n cert-manager \\\n"
        "      -o jsonpath='{.data.tls\\\\.crt}' \\\n"
        "      | base64 -d > certs/homelab-root-ca.crt"
    )

    console.print(
        "[green]Root CA exported to certs/homelab-root-ca.crt[/green]"
    )


@app.command()
def export_ca_cmd() -> None:
    export_ca()


@app.command()
def up() -> None:
    install_tls()


@app.command()
def uninstall() -> None:
    console.print("[red]Teardown not implemented yet[/red]")


if __name__ == "__main__":
    app()
