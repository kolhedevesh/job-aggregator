# Copilot / AI Agent Instructions for job_aggregator

Purpose
- Help an AI coding agent become productive quickly in this repository.

Repository snapshot
- Only discovered files: [.gitignore](.gitignore) (contains `.venv`, `node_modules`, `.env`, `__pycache__`).
- No `README.md`, `package.json`, `requirements.txt`, or obvious source directories were present when this file was created.

First actions (what to run / check)
- Confirm repository contents: `git ls-files` and `ls -la` at project root.
- Look for these common entrypoints and manifest files (stop when found):
  - [package.json](package.json) — Node services
  - [requirements.txt](requirements.txt), [pyproject.toml](pyproject.toml), [Pipfile](Pipfile) — Python deps
  - [Dockerfile](Dockerfile), [Makefile](Makefile), `scripts/` — dev/run helpers
  - `src/`, `app/`, `services/`, `jobs/` — code folders
  - `tests/`, `pytest.ini`, `tox.ini` — test config

If repo is sparse (like now)
- Ask the operator which component they want to work on (API, scraper, CLI, worker). Do not assume architecture.
- Propose a minimal scaffold when asked (e.g., Python service with `src/`, `requirements.txt`, `Dockerfile`) rather than inventing large features.

Architecture discovery checklist (how to quickly infer "big picture")
- Find top-level scripts and manifests (`package.json`, `pyproject.toml`, `Dockerfile`, `Procfile`).
- Open any `src/` or `app/` folders and locate HTTP server entrypoints (`app.py`, `main.py`, `server.js`) and worker scripts (`worker.py`, `tasks.js`).
- Check CI config (`.github/workflows/**`, `.circleci/config.yml`) to learn build/test commands.
- Note any external integrations by scanning for keys/hosts in config files (`.env.example`, `config/*.yml`) — do not use secrets.

Project-specific conventions (discoverable)
- Virtual environments are held in `.venv` (see [.gitignore](.gitignore)); use that when running Python locally.
- `node_modules` is ignored — expect Node projects to use standard `npm`/`yarn` flows if `package.json` appears.

Build, test, and debug guidance (examples to try)
- Python quick setup (if Python manifests exist):
  - `python -m venv .venv && .venv/bin/pip install -r requirements.txt`
  - Run tests: `.venv/bin/pytest -q`
- Node quick setup (if `package.json` exists):
  - `npm ci` or `yarn install`
  - Run tests: `npm test`
- If CI workflows exist, follow the commands used there — they are authoritative for the repo.

When editing or adding files
- If `.github/copilot-instructions.md` already exists, merge conservatively: preserve any CI or policy notes and append missing discovery steps.
- Keep instructions short (20–50 lines). Prefer explicit file/command examples over generic advice.

What *not* to do
- Don’t assume the runtime (Python vs Node) — confirm via manifests before changing code.
- Don’t add or commit secrets; if you find potential secrets, report their path to the operator.

If you need clarification
- Ask one concise question about the intended component or priority (e.g., "Do you want work on an HTTP API, a scraper, or a scheduled worker?").

Key files to reference during work
- [.gitignore](.gitignore) — repo-level ignores and environment hints
- (Look for) [package.json](package.json), [requirements.txt](requirements.txt), [pyproject.toml](pyproject.toml), [Dockerfile](Dockerfile), [.github/workflows/**](.github/workflows)

Next step for the AI agent that created this file
- Report back to the repo owner with the above findings and ask which component to initialize or inspect next.
