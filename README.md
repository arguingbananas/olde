# Olde

What would modern news look like in the English of Chaucer?

Olde reads an English-language RSS feed and shows every headline and summary in
readable Chaucerian Middle English, translated by Claude. Each story links to the
original, and the modern English text is one click away. This is imitation Middle
English for fun, not historically exact scholarship.

## Run it

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
.venv/bin/python olde.py
```

Then open http://127.0.0.1:5000. Stories appear in modern English first and
switch to Middle English as their translations finish.

Run a single process only, because each process would poll the feed on its own.

## Settings

| Variable | Default | Purpose |
|---|---|---|
| `FEED_URL` | BBC News front page | The RSS or Atom feed to read. Feeds that declare a non-English language are rejected. |
| `OLDE_MODEL` | `claude-opus-5-5` | The Claude model used for translation. |
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
