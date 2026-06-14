bootstrap:
	uv run python -m scripts.bootstrap up

platform-up:
	uv run python -m scripts.platform up

platform-down:
	uv run python -m scripts.platform down

downstrap:
	uv run python -m scripts.bootstrap down

status:
	uv run python -m scripts.bootstrap status

destroy:
	./scripts/destroy_env.zsh

ingress:
	uv run python -m scripts.ingress up

hosts:
	uv run python -m scripts.ingress hosts

tls:
	uv run python -m scripts.tls up

reset-tls:
	uv run python -m scripts.tls down

export-ca:
	uv run python -m scripts.tls export-ca

k8sgpt-install:
	uv run python -m scripts.k8sgpt install