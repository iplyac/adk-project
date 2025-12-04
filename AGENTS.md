# Repository Guidelines

## Project Structure & Modules
- Core agent code lives in `my_agent/` (`agent.py`, `devops_agent.py`, `vertex_tools.py`, `session_monitor.py`, `telegram_bot.py`); entrypoint exports sit in `my_agent/__init__.py`.
- FastAPI app and CLI wiring are in `app.py` plus `register_agent.py`; Telegram runner script is `start_bot_service.sh`.
- Static web chat lives under `static/`; CI/deploy scripts: `deploy.sh`, `deploy-local.sh`, `cloudbuild.yaml`, `docker-compose.yml`.
- Tests reside in `tests/` (pytest); sample config in `.env.example`; API key helper file is `api-key`.

## Build, Test, and Development Commands
- Local API + UI: `uvicorn app:app --reload --port 8000` then open `/static/index.html`.
- ADK runner: `adk run my_agent` (use `--web` for browser UI); set `ADK_TEST_MODE=true` to short-circuit LLM calls.
- Unit tests: `pytest tests -v`.
- Docker/Cloud Run: `./deploy.sh` (builds image, pushes, deploys); for local compose: `docker-compose up --build`.

## Coding Style & Naming Conventions
- Python 3.10+, 4-space indentation; prefer type hints and concise docstrings for tools and FastAPI routes.
- Keep modules small: tools in `*tools.py`, service helpers in `secret_manager.py`/`session_monitor.py`, agent setup in `agent.py`.
- Use snake_case for functions/variables, PascalCase for classes, kebab-case for script names. Keep public tool names descriptive (e.g., `get_weather`).

## Testing Guidelines
- Framework: pytest with httpx/pytest-asyncio for async endpoints and tool behaviors.
- Name tests `test_<feature>.py`; fixtures live in `tests/conftest.py`.
- Run `pytest tests -v` before PRs; add focused tests when adding tools, handlers, or session logic.

## Commit & Pull Request Guidelines
- Commit style in history: short, imperative summaries (e.g., “add latency meter”, “switch to webhook”); keep scope focused.
- PRs: include what changed, why, and how to validate (commands or curl examples); link issues if applicable and add screenshots for UI tweaks.
- Avoid committing secrets; ensure `.env`/`api-key` are excluded and Cloud Run secrets are referenced via env IDs.

## Security & Configuration Tips
- Load secrets from Secret Manager via `GOOGLE_API_KEY_SECRET_ID`/`TELEGRAM_BOT_TOKEN_SECRET_ID`; fall back to `.env` only for local dev.
- For DevOps tools, ensure ADC is configured (`gcloud auth application-default login`) or mount service account key (`key.json`) only in secure environments.
- Prefer `TELEGRAM_WEBHOOK_URL` for production; default polling is fine locally.
