import os
import subprocess
import sys
import time

import typer

from scripts.logger import console
from scripts.state import StateManager

app = typer.Typer()
state = StateManager()


# ----------------------------
# Utils
# ----------------------------


def run(cmd: str) -> None:
    """Run shell command safely."""
    console.print(f"[cyan]$ {cmd}[/cyan]")
    result = subprocess.run(cmd, shell=True, text=True)
    if result.returncode != 0:
        console.print(f"[red]Command failed:[/red] {cmd}")
        console.print(result)
        sys.exit(result.returncode)


def command_exists(cmd: str) -> bool:
    return (
        subprocess.run(
            f"command -v {cmd}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def require(cmd: str, name: str) -> None:
    """Ensure tool exists."""
    try:
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL)
        console.print(f"[green]✔ {name} found[/green]")
    except subprocess.CalledProcessError:
        console.print(f"[red]Missing required tool: {name}[/red]")
        sys.exit(1)


def wait_for_vm(name: str, retries: int = 30) -> None:
    """Wait until Multipass VM accepts exec/SSH."""
    console.print(f"[bold]Waiting for VM {name}...[/bold]")

    for i in range(retries):
        result = subprocess.run(
            f"multipass exec {name} -- true",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if result.returncode == 0:
            console.print(f"[green]✔ {name} ready[/green]")
            return

        console.print(f"[yellow]{name} not ready ({i+1}/{retries})[/yellow]")
        time.sleep(5)

    console.print(f"[red]Timeout waiting for {name}[/red]")
    sys.exit(1)


def vm_exists(name: str) -> bool:
    result = subprocess.run(
        f"multipass info {name}",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


# ----------------------------
# Pre-flight checks
# ----------------------------


def check_environment() -> None:
    console.print("[bold]Running environment checks...[/bold]")

    require("python --version", "python")
    require("uv --version", "uv")
    require("git --version", "git")

    console.print("[green]Environment OK[/green]")


def check_cluster_tools() -> bool:
    console.print("[bold]Checking cluster dependencies...[/bold]")

    try:
        subprocess.run(
            "multipass version", shell=True, check=True, stdout=subprocess.DEVNULL
        )
        subprocess.run(
            "multipass launch --help",
            shell=True,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        console.print("[green]✔ multipass found[/green]")
    except subprocess.CalledProcessError:
        console.print("[red]Missing dependency: multipass[/red]")

def init_state() -> None:
    if not state.get("initialized"):
        console.print("[yellow]Initializing state...[/yellow]")
        state.set("initialized", True)


def step_tooling() -> None:
    if state.get("tooling_ready"):
        console.print("[green]Tooling already ready → skipping[/green]")
        return

    console.print("[yellow]Tooling step (placeholder)[/yellow]")
    state.set("tooling_ready", True)


def step_cluster() -> None:
    if state.get("tooling_ready"):
        console.print("[green]Tooling already ready → skipping[/green]")
        return

    console.print("[yellow]Tooling step (placeholder)[/yellow]")
    state.set("tooling_ready", True)


def step_cluster():
    if not check_cluster_tools():
        console.print("[red]Cluster prerequisites missing. Aborting.[/red]")
        return

    if state.get("cluster_ready"):
        console.print("[green]Cluster already ready → skipping[/green]")
        return

    console.print("[bold yellow]Starting cluster provisioning...[/bold yellow]")

    create_vms()
    install_k3s()
    join_worker()
    configure_k3s_kubeconfig_permissions()
    setup_local_kubeconfig()
    validate_cluster()

    state.set("cluster_ready", True)
 -> None:
    console.print("[bold]Creating VMs with Multipass...[/bold]")

    if state.get("vms_created"):
        console.print("[green]VMs already exist → skipping[/green]")
        return

    if not vm_exists("k8s-ctrl"):
        run(
            "multipass launch 24.04 --name k8s-ctrl --cpus 2 "
            "--memory 4G --disk 20G"
        )
    else:
        console.print("[yellow]k8s-ctrl already exists → skipping[/yellow]")

    if not vm_exists("k8s-worker-1"):
        run(
            "multipass launch 24.04 --name k8s-worker-1 --cpus 2 "
            "--memory 4G --disk 50G"
        )
    else:
        console.print("[yellow]k8s-worker-1 already exists → skipping[/yellow]")

    if not vm_exists("k8s-worker-2"):
        run(
            "multipass launch 24.04 --name k8s-worker-2 --cpus 2 "
            "--memory 4G --disk 50G"
        )
    else:
        console.print("[yellow]k8s-worker-2 already exists → skipping[/yellow]")
console.print("[yellow]k8s-worker-2 already exists → skipping[/yellow]")    
        
    wait_for_vm("k8s-ctrl")
    wait_for_vm("k8s-worker-1")
    wait_for_vm(" -> None:
    console.print("[bold]Installing k3s on control plane...[/bold]")

    if state.get("k3s_installed"):
        console.print("[green]k3s already installed → skipping[/green]")
        return

    run(
        "multipass exec k8s-ctrl -- bash -c "
        '"curl -sfL https://get.k3s.io | sh -"'
    )

    # get token
    token = subprocess.check_output(
        "multipass exec k8s-ctrl sudo cat /var/lib/rancher/k3s/server/node-token",
        shell=True,
    # get token
    token = subprocess.check_output(
        "multipass exec k8s-ctrl sudo cat /var/lib/rancher/k3s/server/node-token",
        shell=True
    ).decode().strip()

    state.set("k3s_token", token)
    state.set("k3 -> None:
    console.print("[bold]Joining worker node...[/bold]")

    if state.get("worker_joined"):
        console.print("[green]Worker already joined → skipping[/green]")
        return

    token = state.get("k3s_token")
    if not token:
        console.print("[red]Missing k3s token[/red]")
        return

    worker_cmd = (
        "curl -sfL https://get.k3s.io | "
        "K3S_URL=https://$(multipass info k8s-ctrl | grep IPv4 | "
        "awk '{print $2}'):6443 K3S_TOKEN={token} sh -"
    )

    run(
        f"multipass exec k8s-worker-1 -- bash -c " f'"{worker_cmd}"'
    )

    run(
        f"multipass exec k8s-worker-2 -- bash -c " f'"{worker_cmd}"'
    run( -> None:
    console.print(
        "[bold yellow]Configuring kubectl access in control plane..."
        "[/bold yellow]"
    )

    run(
        "multipass exec k8s-ctrl -- bash -c '\n"
        "mkdir -p ~/.kube &&\n"
        "sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config &&\n"
        "sudo chown ubuntu:ubuntu ~/.kube/config &&\n"
        "chmod 600 ~/.kube/config\n"
        "'"
    )

    console.print("[green]kubectl access configured[/green]")


def setup_local_kubeconfig() -> None:
    console.print("[bold yellow]Configuring local kubeconfig...[/bold yellow]")

    run("mkdir -p ~/.kube")

    ctrl_ip = subprocess.check_output(
        "multipass info k8s-ctrl | awk '/IPv4/ {print $2}'",
        shell=True,
        text=True,
    ).strip()

    run(
        f"multipass exec k8s-ctrl -- sudo cat "
        f"/etc/rancher/k3s/k3s.yaml | sed 's/127.0.0.1/{ctrl_ip}/' "
        f"> ~/.kube/config"
    )

    run("chmod 600 ~/.kube/config")

    console.print("[green]Local kubeconfig configured[/green]")


def validate_cluster() -> None
    )

    run("chmod 600 ~/.kube/config")

    console.print("[green]Local kubeconfig configured[/green]")

def validate_cluster():
    console.print("[bold yellow]Validating cluster access...[/bold yellow]")
    run("kubectl get nodes")
    console.print("[green]Cluster validation successful[/green]")


@app.command()
def up() -> None:
    console.print("[bold green]Homelab bootstrap starting[/bold green]")

    check_environment()

    init_state()
    step_tooling()
    step_cluster()

    console.print("[bold green]Bootstrap complete[/bold green]")


@app.command()
def status() -> None:
    console.print(state.load())


@app.command()
def down() -> None:
    console.print("[red]Teardown not implemented yet[/red]")

    console.print(state.load())


@app.command()
def down():
    console.print("[red]Teardown not implemented yet[/red]")

if __name__ == "__main__":
    app()