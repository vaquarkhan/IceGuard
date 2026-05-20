# Publishing to PyPI

See **[STATUS.md](STATUS.md)** for the full release checklist and manual upload steps for **v0.2.2**.

## Quick manual publish

```bash
pip install build twine
python -m build
twine check dist/*
twine upload dist/*    # or testpypi first
```

## GitHub Actions (optional)

1. Add secret `PYPI_API_TOKEN` in repo Settings → Secrets  
2. Create release tag `v0.2.2`  
3. Workflow `.github/workflows/publish-pypi.yml` uploads `dist/*`

## Package contents

The published wheel contains **only** `iceguard` (under `src/iceguard/`). Tests, Terraform, and examples stay on GitHub, not on PyPI.
