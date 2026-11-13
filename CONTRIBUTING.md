# Contributing to Vortexa Studio

## Development
```bash
pip install -r requirements-dev.txt
pytest -q
python scripts/demo_smoke.py
```

## Branching
- `main` — stable tagged releases
- feature / fix branches → PR into `main`

## Pull requests
- Keep changes focused
- Include tests for behavior changes
- Run the PR checklist in `.github/pull_request_template.md`
- Do not commit `~/`, logs, PIDs, or generated `urdf/*` outputs

## Code of conduct
Be respectful. This is an engineering project — critique ideas, not people.
