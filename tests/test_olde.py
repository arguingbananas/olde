import json
import socket
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import httpx2
import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import anthropic

import olde

NOW = 1_000_000.0


def rss(count=2, ttl=15, language="en-gb"):
    entries = "".join(
        f"<item><title>Story {n}</title><description>Summary {n}</description>"
        f"<link>https://example.com/{n}</link><guid>id-{n}</guid></item>"
        for n in range(count)
    )
    return (
        '<?xml version="1.0"?><rss version="2.0"><channel><title>Test News</title>'
        f"<link>https://example.com</link><language>{language}</language>"
        f"<ttl>{ttl}</ttl>{entries}</channel></rss>"
    ).encode()


def http_response(status=200, content=b"", headers=None):
    response = requests.Response()
    response.status_code = status
    response._content = content
    # Lets iter_content serve the body above, as it does for a streamed download.
    response._content_consumed = True
    response.headers.update(headers or {})
    response.url = olde.FEED_URL
    return response


class FakeFeedServer:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def get(self, url, headers=None, timeout=None, stream=False):
        self.requests.append((url, headers))
        return self.responses.pop(0)


class FakeClaude:
    """Translates every entry, or refuses any batch containing a marked title."""

    def __init__(self, refuse=None, error=None):
        self.refuse = refuse
        self.error = error
        self.batch_sizes = []
        self.requests = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.requests.append(kwargs)
        if self.error:
            raise self.error
        source = json.loads(kwargs["messages"][0]["content"])
        self.batch_sizes.append(len(source))
        if self.refuse and any(entry["title"] == self.refuse for entry in source):
            return SimpleNamespace(stop_reason="refusal", content=[])
        text = json.dumps(
            {
                "translations": [
                    {
                        "id": entry["id"],
                        "title": f"Olde {entry['title']}",
                        "summary": f"Olde {entry['summary']}",
                    }
                    for entry in source
                ]
            }
        )
        return SimpleNamespace(
            stop_reason="end_turn",
            content=[
                SimpleNamespace(type="thinking"),
                SimpleNamespace(type="text", text=text),
            ],
        )


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """Ignore settings from the developer's shell and refuse every real connection."""
    monkeypatch.setattr(olde, "FEED_URL", "https://feed.example/rss")
    monkeypatch.setattr(olde, "PROVIDER", "claude")
    monkeypatch.setattr(olde, "MODEL", olde.DEFAULT_MODELS["claude"])
    monkeypatch.setattr(olde, "STYLE", "kjv")
    monkeypatch.setattr(olde, "OLLAMA_URL", "http://localhost:11434")
    monkeypatch.setattr(olde, "STATE_PATH", tmp_path / "state.json")

    def refuse(*args, **kwargs):
        # pytest.fail is not an Exception, so the app's error handling can't swallow it.
        pytest.fail(f"a test tried to reach the network {args[-1:]}; use the fakes instead")

    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)


@pytest.fixture
def state():
    return olde.new_state()


def use_feed(monkeypatch, *responses):
    server = FakeFeedServer(*responses)
    monkeypatch.setattr(olde.requests, "get", server.get)
    return server


def use_claude(monkeypatch, claude=None):
    claude = claude or FakeClaude()
    monkeypatch.setattr(olde.anthropic, "Anthropic", lambda: claude)
    return claude


def test_keeps_and_translates_every_entry(state, monkeypatch):
    use_feed(monkeypatch, http_response(content=rss(count=60)))
    claude = use_claude(monkeypatch)

    olde.refresh(state, now=NOW)

    assert len(state["items"]) == 60
    assert all(
        olde.translation(item)["me_title"].startswith("Olde Story") for item in state["items"]
    )
    assert claude.batch_sizes == [25, 25, 10]


def test_merges_entries_with_identical_text_and_keeps_the_first(state, monkeypatch):
    feed = (
        b'<?xml version="1.0"?><rss version="2.0"><channel><title>T</title>'
        b"<item><title>Same</title><description>Text</description>"
        b"<link>https://example.com/first</link><guid>a</guid></item>"
        b"<item><title>Other</title><description>Text</description>"
        b"<link>https://example.com/other</link><guid>b</guid></item>"
        b"<item><title>Same</title><description>Text</description>"
        b"<link>https://example.com/second</link><guid>c</guid></item>"
        b"</channel></rss>"
    )
    use_feed(monkeypatch, http_response(content=feed))
    claude = use_claude(monkeypatch)

    olde.refresh(state, now=NOW)

    assert [item["title"] for item in state["items"]] == ["Same", "Other"]
    assert state["items"][0]["link"] == "https://example.com/first"
    assert claude.batch_sizes == [2]


def test_strips_wordpress_footer_from_summaries():
    summary = (
        "<p>The post office reopens today. It has served the town for years [&#8230;]</p>\n"
        '<p>The post <a href="https://example.com/x">Post Office Reopens</a> appeared first on '
        '<a href="https://example.com">The White House</a>.</p>'
    )

    assert olde.clean_summary(summary) == (
        "The post office reopens today. It has served the town for years […]"
    )
    assert olde.clean_summary("The post office reopens today.") == (
        "The post office reopens today."
    )


def test_does_not_fetch_again_before_the_poll_interval(state, monkeypatch):
    server = use_feed(monkeypatch, http_response(content=rss(ttl=30)))
    use_claude(monkeypatch)

    assert olde.refresh(state, now=NOW) is True
    assert state["feed"]["next_fetch_at"] == NOW + 30 * 60
    assert olde.refresh(state, now=NOW + 29 * 60) is False
    assert len(server.requests) == 1


def test_short_ttl_and_max_age_cannot_go_below_the_minimum(state, monkeypatch):
    use_feed(
        monkeypatch,
        http_response(content=rss(ttl=1), headers={"Cache-Control": "max-age=2"}),
    )
    use_claude(monkeypatch)

    olde.refresh(state, now=NOW)

    assert state["feed"]["next_fetch_at"] == NOW + olde.MIN_POLL_SECONDS


def test_long_max_age_extends_the_interval(state, monkeypatch):
    use_feed(
        monkeypatch,
        http_response(content=rss(), headers={"Cache-Control": "public, max-age=7200"}),
    )
    use_claude(monkeypatch)

    olde.refresh(state, now=NOW)

    assert state["feed"]["next_fetch_at"] == NOW + 7200


def test_sends_identity_and_conditional_headers_and_handles_304(state, monkeypatch):
    server = use_feed(
        monkeypatch,
        http_response(
            content=rss(),
            headers={"ETag": '"abc"', "Last-Modified": "Sat, 07 Nov 2026 03:00:00 GMT"},
        ),
        http_response(status=304),
    )
    claude = use_claude(monkeypatch)

    olde.refresh(state, now=NOW)
    olde.refresh(state, now=NOW + olde.MIN_POLL_SECONDS)

    _, first_headers = server.requests[0]
    _, second_headers = server.requests[1]
    assert first_headers["User-Agent"] == olde.USER_AGENT
    assert "If-None-Match" not in first_headers
    assert second_headers["If-None-Match"] == '"abc"'
    assert second_headers["If-Modified-Since"] == "Sat, 07 Nov 2026 03:00:00 GMT"
    assert len(state["items"]) == 2
    assert claude.batch_sizes == [2]


def test_only_new_entries_are_translated(state, monkeypatch):
    use_feed(
        monkeypatch,
        http_response(content=rss(count=2)),
        http_response(content=rss(count=3)),
    )
    claude = use_claude(monkeypatch)

    olde.refresh(state, now=NOW)
    olde.refresh(state, now=NOW + olde.MIN_POLL_SECONDS)

    assert claude.batch_sizes == [2, 1]


def test_honors_retry_after_and_backs_off(state, monkeypatch):
    use_feed(
        monkeypatch,
        http_response(status=429, headers={"Retry-After": "7200"}),
        http_response(status=500),
    )

    olde.refresh(state, now=NOW)
    assert state["feed"]["next_fetch_at"] == NOW + 7200

    olde.refresh(state, now=NOW + 7200)
    assert state["feed"]["next_fetch_at"] == NOW + 7200 + 2 * olde.MIN_POLL_SECONDS


def test_stops_polling_when_feed_is_gone(state, monkeypatch):
    server = use_feed(monkeypatch, http_response(status=410))

    olde.refresh(state, now=NOW)

    assert olde.refresh(state, now=NOW + 10**9) is False
    assert len(server.requests) == 1


def test_network_failure_is_recorded_and_retried_later(state, monkeypatch):
    def fail(*args, **kwargs):
        raise requests.ConnectionError("no route")

    monkeypatch.setattr(olde.requests, "get", fail)

    olde.refresh(state, now=NOW)

    assert "no route" in state["feed"]["feed_error"]
    assert state["feed"]["next_fetch_at"] == NOW + olde.MIN_POLL_SECONDS


def test_oversized_feed_is_not_read_and_retried_later(state, monkeypatch):
    monkeypatch.setattr(olde, "MAX_FEED_BYTES", 100)
    use_feed(monkeypatch, http_response(content=rss(count=5)))
    claude = use_claude(monkeypatch)

    olde.refresh(state, now=NOW)

    assert "larger than" in state["feed"]["feed_error"]
    assert state["items"] == []
    assert state["feed"]["next_fetch_at"] == NOW + olde.MIN_POLL_SECONDS
    assert claude.requests == []


def test_rejects_non_english_feeds_without_calling_claude(state, monkeypatch):
    use_feed(monkeypatch, http_response(content=rss(language="fr")))
    claude = use_claude(monkeypatch)

    olde.refresh(state, now=NOW)

    assert state["items"] == []
    assert "English" in state["feed"]["feed_error"]
    assert claude.batch_sizes == []


def test_refusal_affects_only_the_refused_story(state, monkeypatch):
    use_feed(monkeypatch, http_response(content=rss(count=4)))
    use_claude(monkeypatch, FakeClaude(refuse="Story 2"))

    olde.refresh(state, now=NOW)

    by_title = {item["title"]: olde.translation(item) for item in state["items"]}
    assert by_title["Story 2"]["untranslatable"] is True
    assert by_title["Story 2"]["me_title"] is None
    for title in ("Story 0", "Story 1", "Story 3"):
        assert by_title[title]["me_title"] == f"Olde {title}"


def test_api_failure_keeps_originals_and_retries_next_poll(state, monkeypatch):
    use_feed(monkeypatch, http_response(content=rss()), http_response(status=304))
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    use_claude(monkeypatch, FakeClaude(error=anthropic.APIConnectionError(request=request)))

    olde.refresh(state, now=NOW)

    assert state["feed"]["translation_error"] == "Could not reach Claude."
    assert all(olde.translation(item)["me_title"] is None for item in state["items"])

    use_claude(monkeypatch)
    olde.refresh(state, now=NOW + olde.MIN_POLL_SECONDS)

    assert state["feed"]["translation_error"] is None
    assert all(olde.translation(item)["me_title"] for item in state["items"])


def test_unknown_or_retired_model_says_to_set_olde_model(state, monkeypatch):
    use_feed(monkeypatch, http_response(content=rss()))
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx2.Response(404, request=request)
    error = anthropic.NotFoundError("model not found", response=response, body=None)
    use_claude(monkeypatch, FakeClaude(error=error))

    olde.refresh(state, now=NOW)

    assert olde.MODEL in state["feed"]["translation_error"]
    assert "OLDE_MODEL" in state["feed"]["translation_error"]
    assert all(olde.translation(item)["me_title"] is None for item in state["items"])


def test_missing_credentials_show_a_helpful_message(state, monkeypatch):
    use_feed(monkeypatch, http_response(content=rss()))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("HOME", str(olde.STATE_PATH.parent))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(olde.STATE_PATH.parent))

    olde.refresh(state, now=NOW)

    assert "ANTHROPIC_API_KEY" in state["feed"]["translation_error"]
    assert len(state["items"]) == 2


def test_state_survives_a_restart_so_timing_is_kept(state, monkeypatch):
    use_feed(monkeypatch, http_response(content=rss()))
    use_claude(monkeypatch)

    olde.refresh(state, now=NOW)
    restored = olde.load_state()

    assert restored["feed"]["next_fetch_at"] == NOW + olde.MIN_POLL_SECONDS
    assert all(olde.translation(item)["me_title"] for item in restored["items"])


def test_chaucer_style_uses_its_own_prompt(state, monkeypatch):
    monkeypatch.setattr(olde, "STYLE", "chaucer")
    use_feed(monkeypatch, http_response(content=rss()))
    claude = use_claude(monkeypatch)

    olde.refresh(state, now=NOW)

    system = claude.requests[0]["system"]
    assert system.startswith(olde.CHAUCER_PROMPT)
    assert "King James" not in system
    assert system.endswith(olde.TRANSLATION_RULES)


def test_switching_style_keeps_the_other_styles_translations(state, monkeypatch):
    use_feed(monkeypatch, http_response(content=rss()))
    claude = use_claude(monkeypatch)
    olde.refresh(state, now=NOW)

    monkeypatch.setattr(olde, "STYLE", "chaucer")
    olde.translate_pending(state)

    assert claude.batch_sizes == [2, 2]
    for item in state["items"]:
        assert olde.translation(item, "kjv")["me_title"] == f"Olde {item['title']}"
        assert olde.translation(item, "chaucer")["me_title"] == f"Olde {item['title']}"


def test_translations_saved_before_styles_become_king_james(state):
    old_items = [
        {"key": "a", "title": "A", "summary": "", "link": "", "published": "",
         "me_title": "Lo, A", "me_summary": "", "untranslatable": False},
        {"key": "b", "title": "B", "summary": "", "link": "", "published": "",
         "me_title": None, "me_summary": None, "untranslatable": False},
    ]  # fmt: skip
    olde.STATE_PATH.write_text(json.dumps({**state, "items": old_items}), encoding="utf-8")

    restored = olde.load_state()

    first, second = restored["items"]
    assert first["translations"] == {
        "kjv": {"me_title": "Lo, A", "me_summary": "", "untranslatable": False}
    }
    assert "me_title" not in first
    assert second["translations"] == {}
    assert olde.is_pending(second)


def test_state_file_is_private_to_its_owner(state):
    olde.STATE_PATH.write_text("{}", encoding="utf-8")
    olde.STATE_PATH.chmod(0o664)

    olde.save_state(state)

    assert olde.STATE_PATH.stat().st_mode & 0o777 == 0o600


def test_a_real_connection_fails_the_test(state):
    with pytest.raises(pytest.fail.Exception, match="use the fakes"):
        olde.fetch_feed(state, NOW)


def test_defaults_to_haiku_without_server_side_fallback(state, monkeypatch):
    use_feed(monkeypatch, http_response(content=rss()))
    claude = use_claude(monkeypatch)

    olde.refresh(state, now=NOW)

    request = claude.requests[0]
    assert olde.MODEL == "claude-haiku-5-5"
    assert request["model"] == "claude-haiku-5-5"
    assert "fallbacks" not in request and "betas" not in request


def test_larger_claude_models_use_server_side_fallback(state, monkeypatch):
    monkeypatch.setattr(olde, "MODEL", "claude-opus-5-5")
    use_feed(monkeypatch, http_response(content=rss()))
    claude = use_claude(monkeypatch)

    olde.refresh(state, now=NOW)

    assert claude.requests[0]["fallbacks"] == "default"
    assert claude.requests[0]["betas"] == ["server-side-fallback-2026-07-01"]


def ollama_reply(payload, done_reason="stop"):
    source = json.loads(payload["messages"][1]["content"])
    content = json.dumps(
        {
            "translations": [
                {"id": entry["id"], "title": f"Lo, {entry['title']}", "summary": entry["summary"]}
                for entry in source
            ]
        }
    )
    body = {
        "message": {"role": "assistant", "content": content},
        "done": True,
        "done_reason": done_reason,
    }
    return http_response(content=json.dumps(body).encode())


def use_ollama(monkeypatch, reply=ollama_reply):
    monkeypatch.setattr(olde, "PROVIDER", "ollama")
    monkeypatch.setattr(olde, "MODEL", olde.DEFAULT_MODELS["ollama"])
    calls = []

    def post(url, json=None, timeout=None):
        calls.append((url, json))
        return reply(json)

    monkeypatch.setattr(olde.requests, "post", post)
    return calls


def test_ollama_translates_with_schema_and_system_prompt(state, monkeypatch):
    use_feed(monkeypatch, http_response(content=rss(count=3)))
    calls = use_ollama(monkeypatch)
    monkeypatch.setattr(olde.anthropic, "Anthropic", lambda: pytest.fail("Claude was called"))

    olde.refresh(state, now=NOW)

    url, payload = calls[0]
    assert url == "http://localhost:11434/api/chat"
    assert payload["model"] == "qwen3.5:4b"
    assert payload["stream"] is False
    assert payload["think"] is False
    assert payload["format"] == olde.TRANSLATION_SCHEMA
    assert payload["messages"][0] == {"role": "system", "content": olde.system_prompt()}
    assert [olde.translation(item)["me_title"] for item in state["items"]] == [
        "Lo, Story 0",
        "Lo, Story 1",
        "Lo, Story 2",
    ]


def test_ollama_missing_model_says_how_to_pull_it(state, monkeypatch):
    use_feed(monkeypatch, http_response(content=rss()))
    use_ollama(monkeypatch, reply=lambda payload: http_response(status=404))

    olde.refresh(state, now=NOW)

    assert state["feed"]["translation_error"] == (
        "Ollama has no model qwen3.5:4b; run: ollama pull qwen3.5:4b"
    )
    assert all(olde.translation(item)["me_title"] is None for item in state["items"])


def test_ollama_not_running_is_reported(state, monkeypatch):
    use_feed(monkeypatch, http_response(content=rss()))

    def refuse(payload):
        raise requests.ConnectionError("connection refused")

    use_ollama(monkeypatch, reply=refuse)

    olde.refresh(state, now=NOW)

    assert "Is it running?" in state["feed"]["translation_error"]


def test_ollama_output_cut_off_splits_the_batch(state, monkeypatch):
    use_feed(monkeypatch, http_response(content=rss(count=2)))
    use_ollama(
        monkeypatch,
        reply=lambda payload: ollama_reply(
            payload, "length" if len(json.loads(payload["messages"][1]["content"])) > 1 else "stop"
        ),
    )

    olde.refresh(state, now=NOW)

    assert all(olde.translation(item)["me_title"].startswith("Lo, ") for item in state["items"])


def test_page_view_never_fetches_and_shows_translation_and_attribution(state, monkeypatch):
    use_feed(monkeypatch, http_response(content=rss()))
    use_claude(monkeypatch)
    olde.refresh(state, now=NOW)

    def forbidden(*args, **kwargs):
        raise AssertionError("page views must not fetch the feed")

    monkeypatch.setattr(olde.requests, "get", forbidden)
    monkeypatch.setattr(olde, "shared_state", state)
    monkeypatch.setattr(olde, "state_lock", threading.Lock())

    body = olde.app.test_client().get("/").get_data(as_text=True)

    assert "Olde Story 0" in body
    assert "Summary 0" in body
    assert 'href="https://example.com/0"' in body
    assert "Test News" in body
    assert "unofficial machine translation into imitation King James English" in body
    assert "English of King James" in body


def test_page_names_the_chaucer_style(state, monkeypatch):
    monkeypatch.setattr(olde, "STYLE", "chaucer")
    monkeypatch.setattr(olde, "shared_state", state)

    body = olde.app.test_client().get("/").get_data(as_text=True)

    assert "English of Chaucer" in body
    assert "imitation Chaucerian Middle English" in body
    assert "King James" not in body


def test_unsafe_links_are_dropped_and_markup_is_escaped(state, monkeypatch):
    feed = (
        b'<?xml version="1.0"?><rss version="2.0"><channel><title>T</title>'
        b"<item><title>A &amp;lt;script&amp;gt;x&amp;lt;/script&amp;gt; B</title>"
        b"<link>javascript:alert(1)</link><guid>1</guid></item></channel></rss>"
    )
    use_feed(monkeypatch, http_response(content=feed))
    use_claude(
        monkeypatch,
        FakeClaude(
            error=anthropic.APIConnectionError(
                request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
            )
        ),
    )
    olde.refresh(state, now=NOW)
    monkeypatch.setattr(olde, "shared_state", state)

    body = olde.app.test_client().get("/").get_data(as_text=True)

    assert state["items"][0]["link"] == ""
    assert "javascript:" not in body
    assert "<script" not in body


def test_quality_check_flags_lost_facts_and_unchanged_text():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import check_translations

    story = {"title": "Rovers win 3-1", "summary": "", "keep": ["Rovers"]}
    good = {"me_title": "Rovers hath won 3-1", "me_summary": ""}
    assert check_translations.problems_with(story, good) == []

    bad = {"me_title": "Rovers win 3-1", "me_summary": "And there was joy."}
    assert check_translations.problems_with(story, bad) == [
        "headline unchanged",
        "empty summary was filled in",
    ]
    assert check_translations.problems_with(story, {"me_title": "They won", "me_summary": ""}) == [
        "lost 'Rovers'",
        "lost '3-1'",
    ]
