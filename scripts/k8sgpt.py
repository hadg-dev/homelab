import os
import shutil
import subprocess
from enum import Enum

import typer

app = typer.Typer()


class Provider(str, Enum):
    openai = "openai"
    gemini = "gemini"
    claude = "claude"


# -------------------------
# utils
# -------------------------


def run_cmd(cmd: list[str]) -> str:
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return result.stdout


def is_installed(binary: str) -> bool:
    return shutil.which(binary) is not None


# -------------------------
# INSTALL
# -------------------------


def install_k8sgpt() -> None:
    """Install K8sGPT binary if not already installed."""

    if is_installed("k8sgpt"):
        typer.echo("K8sGPT already installed.")
        return

    typer.echo("Installing K8sGPT...")

    install_script = (
        "https://raw.githubusercontent.com/k8sgpt-ai/k8sgpt/main/install.sh"
    )

    run_cmd(["bash", "-c", f"curl -s {install_script} | bash"])

    typer.echo("K8sGPT installed successfully.")


# -------------------------
# AUTH
# -------------------------


def configure_provider(provider: Provider) -> None:
    """Configure LLM backend for K8sGPT."""

    if provider == Provider.openai:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY missing")

        run_cmd(["k8sgpt", "auth", "add", "openai", "--api-key", key])

    elif provider == Provider.gemini:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY missing")

        run_cmd(["k8sgpt", "auth", "add", "google", "--api-key", key])

    elif provider == Provider.claude:
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY missing")

        run_cmd(["k8sgpt", "auth", "add", "anthropic", "--api-key", key])


# -------------------------
# CLI
# -------------------------


@app.command()
def install() -> None:
    """Install K8sGPT binary."""
    install_k8sgpt()


if __name__ == "__main__":
    app()
