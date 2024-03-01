from flask import Flask, render_template
import feedparser
from openai import OpenAI
import os

# Read the OpenAI API key from the environment variable
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Read the feed limit from the environment variable or set a default value
FEED_LIMIT = int(os.environ.get("FEED_LIMIT", "5"))  # Default to 5 articles

# Check if the API key is provided
if not OPENAI_API_KEY:
    raise ValueError(
        "Please provide your OpenAI API key in the OPENAI_API_KEY environment variable."
    )

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)


def translate_text(input_text, target_language="fr"):
    # Define the prompt for translation
    prompt = "Translate the following English text into Shakespearean English"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": input_text},
        ],
    )
    return response.choices[0].message.content


def translate_feed(feed):
    translated_feed = {}

    # Translate feed title and description
    translated_feed["title"] = translate_text(feed["title"])
    translated_feed["description"] = translate_text(feed["description"])
    translated_feed["link"] = feed["link"]
    translated_feed["entries"] = []

    # Translate and limit the number of entries in the feed
    for entry in feed["entries"][:FEED_LIMIT]:
        translated_entry = {
            "title": translate_text(entry["title"]),
            "summary": translate_text(entry["summary"]),
        }
        translated_feed["entries"].append(translated_entry)

    return translated_feed


@app.route("/")
def index():
    rss_feed_url = "http://feeds.bbci.co.uk/news/rss.xml"
    feed = read_rss(rss_feed_url)
    translated_feed = translate_feed(feed)
    return render_template("index.html", feed=translated_feed)


def read_rss(feed_url):
    # Parse the RSS feed
    feed = feedparser.parse(feed_url)

    # Prepare the feed data
    feed_data = {
        "title": feed.feed.title,
        "description": feed.feed.description,
        "link": feed.feed.link,
        "entries": [],
    }

    # Limit the number of articles fetched
    for entry in feed.entries[:FEED_LIMIT]:
        entry_data = {"title": entry.title, "summary": entry.get("summary", "")}
        feed_data["entries"].append(entry_data)

    return feed_data


if __name__ == "__main__":
    app.run(debug=True)
