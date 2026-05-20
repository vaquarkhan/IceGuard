# Docker image

IceGuard publishes a **Lambda + PySpark** container image to GitHub Container Registry (GHCR).

| Registry | Image |
|----------|--------|
| GHCR | `ghcr.io/vaquarkhan/iceguard` |

Tags: `1.0.0`, `latest` (and the version matching each GitHub Release).

## Pull

```bash
docker pull ghcr.io/vaquarkhan/iceguard:1.0.0
docker pull ghcr.io/vaquarkhan/iceguard:latest
```

## What is in the image

- Base: `public.ecr.aws/lambda/python:3.12`
- Java 17 (Corretto) for PySpark
- `iceguard[spark,iceberg,otel]` at the version baked into the tag
- Sample handler from `examples/sam/handler.py` (replace with your code)

## Use as a Lambda container base

```dockerfile
FROM ghcr.io/vaquarkhan/iceguard:1.0.0

COPY my_handler.py ${LAMBDA_TASK_ROOT}/
CMD ["my_handler.lambda_handler"]
```

Deploy with AWS Lambda container image support (ECR pull from GHCR, or copy to your account ECR).

## Run locally (smoke test)

```bash
docker run --rm -p 9000:8080 \
  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_DEFAULT_REGION \
  ghcr.io/vaquarkhan/iceguard:1.0.0
```

Invoke: `curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'`

## Build locally

```bash
docker build --build-arg ICEGUARD_VERSION=1.0.0 -t iceguard:local .
```

## Publish (maintainers)

Workflow `.github/workflows/publish-docker.yml` runs on **GitHub Release** (same tag as PyPI) or **workflow_dispatch** with a version input.

Images are public at: https://github.com/vaquarkhan/IceGuard/pkgs/container/iceguard
