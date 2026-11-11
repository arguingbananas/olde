# Olde

What would modern news look like in the English of the King James Bible?¹

Olde reads an English-language RSS feed and shows every headline and summary in
King James English, translated by Claude or by a local model through Ollama:
period grammar such as "hath", "-eth" and "unto", with modern spelling so it
stays easy to read. Each story links to the original, and the modern English
text is one click away. This is imitation Early Modern English for fun, not
historically exact scholarship.

It's a personal project for one reader, running on their own computer and
viewed in a browser. It isn't built to be hosted for the public.

## Run it

Olde needs Python 3.12 or newer. It's developed and tested on Linux (Linux Mint
22.3) and should run anywhere Python does. Only the Ollama option cares about
hardware.

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
.venv/bin/python olde.py
```

Then open http://127.0.0.1:5000. Stories appear in modern English first and
switch to King James English as their translations finish.

With Claude Haiku, translation costs about $0.00025 per story (measured on real
news feeds, plus about 30% for the high effort setting). A busy
feed with about 100 new stories a day comes to roughly $0.75 a month. Set a
spending limit in the Anthropic Console to be safe.

Run a single process only, because each process would poll the feed on its own.

### With Ollama instead of Claude

Ollama runs a model on your own machine, so translations cost nothing and
need no API key. Install it from https://ollama.com, then:

```
ollama pull qwen3.5:4b
OLDE_PROVIDER=ollama .venv/bin/python olde.py
```

`qwen3.5:4b` stayed the most faithful to the news among the small models we
tried (`llama3.2`, `gemma3:4b` and `phi4-mini` all added or changed facts), but
its King James English is stilted. On a 4 GB GPU it runs partly on the CPU and
takes about a minute per batch. Thinking is turned off, because it otherwise
spends many minutes on one batch. Larger models translate better if your
hardware can run them; choose one with `OLDE_MODEL`.

Translations are saved by story, so switching provider keeps the ones you
already have. To compare providers, give each its own state file, for example
`OLDE_STATE=.cache/ollama.json`, and run one at a time.

## Settings

| Variable | Default | Purpose |
|---|---|---|
| `FEED_URL` | White House news releases | The RSS or Atom feed to read. Feeds that declare a non-English language are rejected. |
| `OLDE_PROVIDER` | `claude` | `claude` or `ollama`. |
| `OLDE_MODEL` | `claude-haiku-5-5`, or `qwen3.5:4b` with Ollama | The model used for translation. |
| `OLDE_OLLAMA_URL` | `http://localhost:11434` | Where the Ollama server is running. |
| `OLDE_STATE` | `.cache/olde.json` | Where feed state and translations are saved. |

`.env.example` lists them all. Copy it to `.env`, fill it in, and load it with
`set -a; . ./.env; set +a` before starting Olde. `.env` is git-ignored.

## How it treats the feed

- One background worker fetches the feed. Page views only read saved state.
- It waits at least 15 minutes between fetches, or longer if the feed's `ttl` or
  `Cache-Control: max-age` asks for it. That timing survives restarts.
- It sends a descriptive `User-Agent` and uses `ETag` and `Last-Modified` when the
  feed provides them.
- It honors `Retry-After`, backs off after failures for up to 6 hours, follows
  permanent redirects, and stops polling on `410 Gone`.
- It doesn't fetch article pages, hotlink images, or republish a feed.
- It stops reading a feed larger than 5 MB and tries again later.
- It credits the source and links each story to the original article.

Only new or changed stories are sent to the model, in batches of 25.

## Privacy

Olde collects nothing about you: no accounts, cookies or analytics, and the page
is only reachable from your own computer. The only data it sends anywhere is
the feed's headlines and summaries, which go to Anthropic for translation (or
stay on your machine with Ollama). Requests to the feed carry Olde's
`User-Agent` and nothing else about you. Feed text and translations are kept in
the state file until stories drop out of the feed; delete `.cache/` to clear
them.

## About the default feed

Olde reads the White House news feed by default because its text is free to
translate. Works of the US federal government aren't protected by copyright
(17 U.S.C. § 105), so translating and altering them needs no permission. Two
limits remain: material a release quotes from someone else, such as an article
or a photo, may still be copyrighted, and the White House name and seal can't
be used to suggest endorsement. The page says it is unofficial and unaffiliated.

The feed is the administration's own publicity, not neutral news, and Olde
translates it as written.

If you point `FEED_URL` at another source, check its terms first: many news
feeds forbid altering their content or sending it to an AI service. Olde binds
to `127.0.0.1` so it stays private by default.

## Development

Install the development tools, then run the tests, the linter, the formatter
and the dependency vulnerability scan:

```
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
.venv/bin/ruff check .
.venv/bin/ruff format .
.venv/bin/pip-audit -r requirements-dev.txt
```

The tests use fake feed and model servers, so they never contact the live feed or a
paid API. The full suite takes a few seconds; run it after every change.
GitHub Actions runs the same checks on every push, and Dependabot proposes
dependency updates weekly. Bug-fix (patch) updates merge themselves once those
checks pass; minor and major updates wait for a person to review them.

After changing the prompt or the model, run the translation check. It
translates eight invented stories with the real model (well under a cent with
Haiku), prints them for reading, and flags lost names or numbers, unchanged
headlines and filled-in empty summaries:

```
.venv/bin/python scripts/check_translations.py
```

Work happens on `main`. Commit subjects are short, in the imperative mood
("Strip the WordPress footer from feed summaries"), and commits use the
GitHub noreply address.

## License

MIT. See [LICENSE](LICENSE).

---

¹ The entire project — concept, specification, and code — was an original human idea written by an artificial intelligence.
