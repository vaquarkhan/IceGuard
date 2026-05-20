# Publishing to PyPI

## Maintainer release

1. Bump version in `pyproject.toml`
2. Tag: `git tag v0.2.0 && git push origin v0.2.0`
3. Create GitHub Release (triggers `.github/workflows/publish-pypi.yml`)
4. Set repository secret `PYPI_API_TOKEN` (pypi.org → Account → API tokens)

## Local dry run

```bash
pip install build twine
python -m build
twine check dist/*
twine upload --repository testpypi dist/*   # optional TestPyPI first
```

## First-time PyPI project

Register the name `iceguard` on PyPI or use `iceguard-lake` if taken.
