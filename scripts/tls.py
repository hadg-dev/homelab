import typer
from rich import print
from pathlib import Path

from scripts.bootstrap import run

app = typer.Typer()

def install_cert_manager():
    run("""
helm repo add jetstack https://charts.jetstack.io || true
helm repo update
""")

    run("""
helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set crds.enabled=true
""")

def install_tls():
    print("[bold yellow]Applying TLS manifests...[/bold yellow]")

    install_cert_manager()
    run("""
    kubectl wait \
    --for=condition=Available \
    deployment/cert-manager \
    -n cert-manager \
    --timeout=300s
    """)
    run("kubectl apply -f k8s/security/")

    print("[green]TLS configured[/green]")


def export_ca():
    Path("certs").mkdir(exist_ok=True)

    run("""
    kubectl get secret homelab-root-ca-secret \
      -n cert-manager \
      -o jsonpath='{.data.tls\\.crt}' \
      | base64 -d > certs/homelab-root-ca.crt
    """)

    print(
        "[green]Root CA exported to certs/homelab-root-ca.crt[/green]"
    )


@app.command()
def export_ca_cmd():
    export_ca()


@app.command()
def up():
    install_tls()

@app.command()
def uninstall():
    console.print("[red]Teardown not implemented yet[/red]")

if __name__ == "__main__":
    app()
