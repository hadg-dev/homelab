import typer
from rich import print
import subprocess
from scripts.bootstrap import run

app = typer.Typer()


def install_ingress():
    print("[bold yellow]Deploying ingress layer...[/bold yellow]")

    run("kubectl apply -f k8s/ingress/")

    print("[green]Ingress deployed[/green]")


@app.command()
def up():
    install_ingress()


@app.command()
def hosts():
    lb_ip = subprocess.check_output(
    "kubectl get svc -n kube-system traefik "
    "-o jsonpath='{.status.loadBalancer.ingress[0].ip}'",
    shell=True,
    text=True,
).strip()

    print(
        f"{lb_ip} argocd.local grafana.local prometheus.local"
    )

if __name__ == "__main__":
    app()