from flask import Flask, render_template, abort
import feedparser
from ollama import Client
import os

# Read the feed limit from the environment variable or set a default value
FEED_LIMIT = int(os.environ.get("FEED_LIMIT", "5"))  # Default to 5 articles

HOST_ADDRESS = os.environ.get(
    "HOST_ADDRESS", "http://localhost:11434"
)  # Default to localhost

app = Flask(__name__)

client = Client(host=HOST_ADDRESS)


def translate_text(input_text, target_language="French", model="phi"):
    try:
        # Define the prompt for translation
        prompt = f"Translate the user input into {target_language}."

        response = client.chat(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": input_text},
            ],
        )
        return response["message"]["content"]
    except Exception as e:
        # Handle translation errors
        return f"Translation Error: {str(e)}"


def translate_feed(feed):
    translated_feed = {}

    try:
        # Translate feed title and description
        translated_feed["title"] = translate_text(feed["title"])
        translated_feed["description"] = translate_text(feed["description"])
        translated_feed["link"] = feed["link"]
        translated_feed["entries"] = []

        # Translate and limit the number of entries in the feed
        for entry in feed["entries"][:FEED_LIMIT]:
            translated_entry = {
                "title": translate_text(entry["title"]),
                "summary": translate_text(entry.get("summary", "")),
            }
            translated_feed["entries"].append(translated_entry)

        return translated_feed
    except Exception as e:
        # Handle translation errors
        abort(500, f"Translation Error: {str(e)}")


@app.route("/")
def index():
    rss_feed_url = "http://feeds.bbci.co.uk/news/rss.xml"
    feed = feedparser.parse(rss_feed_url)
    translated_feed = translate_feed(feed)
    return render_template("index.html", feed=translated_feed)


if __name__ == "__main__":
    app.run(debug=True)
