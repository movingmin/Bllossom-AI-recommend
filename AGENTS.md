# Repository Guidelines

## Project Structure & Module Organization
- `crawling/` houses the news-ingestion pipeline (Dockerfile, `requirements.txt`, entry `main.py`, helpers like `news_crawler.py`, `analyze.py`, and data assets in `db/`).
- `calling_api/` will hold service stubs that expose processed signals, while `Web/` contains the web client scaffold.
- Keep generated data (`crawling/db/*.json`) out of Git—use `.gitignore` defaults and your own local backups for large or sensitive artifacts.

## Build, Test, and Development Commands
- Python env: `python3 -m venv .venv && source .venv/bin/activate` followed by `pip install -r crawling/requirements.txt`.
- Run crawler end-to-end: `python crawling/main.py` (fetches articles, writes `crawling.json`, triggers analysis).
- Container workflow: `docker build -t xai-crawling ./crawling` then `docker run --rm -v $(pwd)/crawling/db:/app/db xai-crawling`.
- Lint pass (recommended): `python -m compileall crawling` to catch syntax errors before commits.

## Coding Style & Naming Conventions
- Python modules use 4-space indentation, lowercase_with_underscores for files/functions, and UpperCamelCase for classes.
- Keep crawler steps pure and side-effect free except for explicit I/O helpers (`db/`, `log/`).
- Log to `crawling/log/main.log` with concise, time-stamped messages so downstream agents can diff behavior quickly.

## Testing Guidelines
- There is no formal test suite yet; smoke-test scripts by running `python news_crawler.py` and `python analyze.py` individually with sampled `db/crawling_labeled.json`.
- Use temporary outputs under `crawling/db/tmp/` (gitignored) when experimenting to avoid corrupting checked-in datasets.
- Aim for parity between KR and EN tickers; validate sentiment scores by spot-checking a few entries in `response.json`.

## Commit & Pull Request Guidelines
- Base commits on `movingmin` and keep messages short and descriptive (e.g., `feat: add kr finbert analyzer`, `fix: handle kosdaq fallback`); avoid committing large JSON dumps.
- Reference related issues in the body (`Fixes #12`) and summarize crawler impact (records touched, APIs invoked).
- PRs should describe manual test steps, include command logs when touching Docker or data flows, and attach screenshots for front-end changes.

## Security & Configuration Tips
- Store API tokens in `.env` or OS keychains; never in tracked files.
- Large datasets must stay local or in object storage—if you accidentally commit them, rewrite history with `git filter-repo` before pushing.
- Keep Docker dependencies minimal (pin versions in `requirements.txt`) to ensure reproducible crawls and sentiment runs.
