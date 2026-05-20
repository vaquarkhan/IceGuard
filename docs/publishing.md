# Publishing to PyPI

**v1.0.0+** uses [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/) (GitHub Actions OIDC). No long-lived API token is required in the repo.

## Trusted publisher (configured on PyPI)

| Field | Value |
|--------|--------|
| PyPI project | `iceguard` |
| Owner | `vaquarkhan` |
| Repository | `IceGuard` |
| Workflow | `publish-pypi.yml` |
| Environment | `pypi` |

Ensure **Settings → Environments → `pypi`** exists on the GitHub repo.

## Publish a new version

1. Bump `version` in `pyproject.toml` (single source of truth; `iceguard.__version__` reads it from package metadata).
2. Commit and push to `main`.
3. Create a GitHub Release with tag `vX.Y.Z` (e.g. `v1.0.0`) and publish it — workflow `.github/workflows/publish-pypi.yml` runs on `release: published`.
4. Or run **Actions → Publish to PyPI → Run workflow** (`workflow_dispatch`).

## Manual publish (fallback)

```bash
pip install build twine
python -m build
twine check dist/*
twine upload dist/*
```

## Docker image (GHCR)

Workflow `.github/workflows/publish-docker.yml` pushes to **`ghcr.io/vaquarkhan/iceguard`** on each GitHub Release (or manual dispatch).

| Item | Value |
|------|--------|
| Registry | `ghcr.io` |
| Image | `vaquarkhan/iceguard` |
| Tags | `X.Y.Z`, `latest` |
| Base | `public.ecr.aws/lambda/python:3.12` + Java 17 + `iceguard[spark,iceberg,otel]` |

See [docker.md](docker.md) for pull and Lambda usage.

## Package contents

The published wheel contains **only** `iceguard` (under `src/iceguard/`). Tests, Terraform, and examples stay on GitHub, not on PyPI.
