"""Translate a fixed set of invented stories and check the results.

Run this after changing the prompt or the model. It uses the same provider and
model settings as the app, so it calls the real model: with Claude Haiku a run
costs well under a cent. Every story is printed for reading, and the script
exits with status 1 if any automatic check fails.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import olde

SAMPLES = Path(__file__).with_name("sample_stories.json")
NUMBER = re.compile(r"\d[\d,.%-]*\d%?|\d%?")


def problems_with(story, result):
    """Return a list of the ways a translation breaks the prompt's rules."""
    if result.get("untranslatable"):
        return ["the model declined to translate it"]
    if not result.get("me_title"):
        return ["no translation came back"]

    title, summary = result["me_title"], result["me_summary"]
    found = []
    if title == story["title"]:
        found.append("headline unchanged")
    if story["summary"] and summary == story["summary"]:
        found.append("summary unchanged")
    if not story["summary"] and summary:
        found.append("empty summary was filled in")
    text = f"{title}\n{summary}".lower()
    numbers = NUMBER.findall(f"{story['title']} {story['summary']}")
    for term in dict.fromkeys(story["keep"] + numbers):
        if term.lower() not in text:
            found.append(f"lost {term!r}")
    return found


def main():
    stories = json.loads(SAMPLES.read_text())
    items = [{"key": str(index), **story} for index, story in enumerate(stories)]
    results = olde.translate_items(olde.make_translator(), items)

    failures = 0
    for item in items:
        result = results.get(item["key"], {})
        problems = problems_with(item, result)
        failures += bool(problems)
        print(f"\n{'FAIL' if problems else 'ok'}  {item['title']}")
        print(f"      {result.get('me_title')}")
        if item["summary"] or result.get("me_summary"):
            print(f"      {result.get('me_summary')}")
        for problem in problems:
            print(f"      - {problem}")

    print(f"\n{olde.PROVIDER} {olde.MODEL}: {len(items) - failures}/{len(items)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
