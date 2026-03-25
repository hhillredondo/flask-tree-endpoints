# Trees API (Flask + Neptune)

## Run locally

```
flask --debug run
```

## Documentation
- `docs/architecture.md`
- `docs/api_endpoints.md`
- `docs/smoke_tests.md`

## Tests

From the repository root (so imports like `config` resolve):

```
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

If you still see `ModuleNotFoundError: No module named 'config'`, use `python -m pytest` or set `PYTHONPATH=`.

If route tests fail with `AttributeError: module 'werkzeug' has no attribute '__version__'`, your environment has **Werkzeug 3** with **Flask 2.3**. Reinstall deps so `requirements.txt` can pin **Werkzeug 2.x** (or use a virtualenv and install only this project’s requirements):

```
pip install -r requirements.txt -r requirements-dev.txt
```

## Lint
```
ruff check .
```

## CI/CD

- **`.github/workflows/test.yml`** — Runs lint + tests on every PR and push to `main`/`master`.
- **`.github/workflows/deploy.yml`** — Manual deploy to ECR/ECS (runs tests before building).

### Branch protection (manual setup)

Enable these rules on `main`/`master` in GitHub repo Settings > Branches:

1. **Require status checks to pass before merging** — select the `test` workflow job.
2. **Require branches to be up to date before merging**.
