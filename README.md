# Olde

What would modern news look like in the English of the King James Bible?

Olde reads an English-language RSS feed and shows every headline and summary in
King James English, translated by Claude or by a local model through Ollama:
period grammar such as "hath", "-eth"
and "unto", with modern spelling so it stays easy to read. Each story links to
the original, and the modern English text is one click away. This is imitation
Early Modern English for fun, not historically exact scholarship.

## Run it

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
.venv/bin/python olde.py
```

Then open http://127.0.0.1:5000. Stories appear in modern English first and
switch to King James English as their translations finish.

Run a single process only, because each process would poll the feed on its own.

### With Ollama instead of Claude

Ollama runs a model on your own machine, so translations cost nothing and
need no API key. Install it from https://ollama.com, then:

```
ollama pull llama3.2
OLDE_PROVIDER=ollama .venv/bin/python olde.py
```

`llama3.2` is a 3B model that fits on a 4 GB GPU. Larger models translate
better if your hardware can run them; choose one with `OLDE_MODEL`.

Translations are saved by story, so switching provider keeps the ones you
already have. To compare providers, give each its own state file, for example
`OLDE_STATE=.cache/ollama.json`, and run one at a time.

## Settings

| Variable | Default | Purpose |
|---|---|---|
| `FEED_URL` | BBC News front page | The RSS or Atom feed to read. Feeds that declare a non-English language are rejected. |
| `OLDE_PROVIDER` | `claude` | `claude` or `ollama`. |
| `OLDE_MODEL` | `claude-haiku-5-5`, or `llama3.2` with Ollama | The model used for translation. |
| `OLDE_OLLAMA_URL` | `http://localhost:11434` | Where the Ollama server is running. |
| `OLDE_STATE` | `.cache/olde.json` | Where feed state and translations are saved. |

## How it treats the feed

- One background worker fetches the feed. Page views only read saved state.
- It waits at least 15 minutes between fetches, or longer if the feed's `ttl` or
  `Cache-Control: max-age` asks for it. That timing survives restarts.
- It sends a descriptive `User-Agent` and uses `ETag` and `Last-Modified` when the
  feed provides them.
- It honors `Retry-After`, backs off after failures for up to 6 hours, follows
  permanent redirects, and stops polling on `410 Gone`.
- It doesn't fetch article pages, hotlink images, or republish a feed.
- It credits the source and links each story to the original article.

Only new or changed stories are sent to Claude, in batches of 25.

## Using the BBC feed

The BBC feed's terms are at
https://www.bbc.co.uk/usingthebbc/terms-of-use/#15metadataandrssfeeds. Read them
before you host this anywhere public or use it commercially, because this app
sends feed text to an AI service and displays altered versions of it. Olde binds
to `127.0.0.1` so it stays private by default.

## Tests

```
.venv/bin/pip install pytest
.venv/bin/python -m pytest
```
