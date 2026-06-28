import subprocess

import typer

from scripts.bootstrap import run
from scripts.logger import console

app = typer.Typer()


def install_ingress() -> None:
    console.print("[bold yellow]Deploying ingress layer...[/bold yellow]")

    run("kubectl apply -f k8s/ingress/")

    console.print("[green]Ingress deployed[/green]")


@app.command()
def up() -> None:
    install_ingress()


@app.command()
def hosts() -> None:
    lb_ip = subprocess.check_output(
        "kubectl get svc -n kube-system traefik "
        "-o jsonpath='{.status.loadBalancer.ingress[0].ip}'",
        shell=True,
        text=True,
    ).strip()

    console.print(f"{lb_ip} argocd.local grafana.local prometheus.local")


if __name__ == "__main__":
    app()