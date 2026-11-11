# Olde

Olde is a small Flask app that reads one English-language RSS feed (White House
news releases by default) and shows every headline and summary in imitation
King James English.
Translation is done by Claude Haiku (`claude-haiku-5-5`, the default) or by a
local Ollama model (`qwen3.5:4b`). It's a personal project for one reader on
their own computer, bound to 127.0.0.1, and not meant for public hosting.

- Input: the feed, fetched politely by one background worker.
- Output: a page at http://127.0.0.1:5000 with the King James text, the modern
  text behind a toggle, and links to the original stories.
- State: feed metadata and translations are saved in `.cache/olde.json`.

## Environment

- Python 3.12 or newer, in a virtualenv at `.venv/`.
- Settings come from environment variables; `.env.example` lists them.
- Claude needs `ANTHROPIC_API_KEY`. Ollama needs a running Ollama server.

## Commands

```
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt   # runtime and dev tools
.venv/bin/python olde.py                        # run the app
.venv/bin/python -m pytest                      # full test suite, a few seconds
.venv/bin/ruff check .                          # lint
.venv/bin/ruff format .                         # format (100 columns)
.venv/bin/pip-audit -r requirements-dev.txt     # dependency vulnerability scan
.venv/bin/python scripts/check_translations.py  # translation quality check (paid)
```

Nothing needs building. The full suite is fast enough to serve as the smoke
test after every change. Run the translation check after any change to the
prompt or the model.

## Rules

- Secrets and personal data never go in code, logs, commits, the state file or
  this file. Don't print or echo API keys.
- Tests must never contact the live feed or a paid API; use the fakes in
  `tests/test_olde.py`.
- Don't fetch the live feed during development unless asked. To try the app,
  serve a saved copy locally (`python3 -m http.server`), point `FEED_URL` at it,
  and use a separate `OLDE_STATE` file.
- Calls to Claude cost money. Say so before starting anything larger than the
  translation check.
- Keep the polling rules intact: 15-minute minimum, conditional requests,
  `ttl`/`max-age`, `Retry-After`, backoff, `410 Gone`, descriptive User-Agent.
- Respect the feed's terms. Don't fetch article pages, hotlink images or
  republish the feed. Keep attribution and links to the original stories.
- Translations must stay faithful: no added, dropped or changed facts. Names,
  places, numbers and dates are kept exactly, and modern terms such as
  "artificial intelligence" stay as written.
- Work on `main`. Commit subjects are short and in the imperative mood.

## Files

Required:

- `olde.py`: the whole app (feed polling, translation, Flask route)
- `templates/index.html`, `static/style.css`: the page
- `tests/test_olde.py`: the test suite
- `scripts/check_translations.py`, `scripts/sample_stories.json`: the
  translation quality check and its invented stories
- `requirements.txt`, `requirements-dev.txt`: pinned dependencies
- `pyproject.toml`: ruff settings
- `README.md`, `LICENSE` (MIT), `SECURITY.md`, `.env.example`, `.gitignore`,
  `CLAUDE.md`
- `.github/workflows/ci.yml`: runs lint, format check, tests and `pip-audit`
  on every push, with no API key
- `.github/dependabot.yml`: weekly grouped updates for pip and the CI actions
- `.github/workflows/dependabot-auto-merge.yml`: squash-merges Dependabot
  patch updates once CI passes; minor and major updates wait for review

Optional, not present yet: CHANGELOG, CONTRIBUTING, ARCHITECTURE notes,
ROADMAP, packaging or Docker, benchmarks.

## Definition of done

- `.venv/bin/python -m pytest` passes.
- `.venv/bin/ruff check .` is clean and `.venv/bin/ruff format --check .`
  reports nothing to change.
- `.venv/bin/pip-audit -r requirements-dev.txt` shows no new high-severity
  findings.
- The README is updated if behavior, settings or commands changed.
